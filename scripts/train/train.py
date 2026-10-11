import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNTIME = ROOT / "models/Garments2Look-LoRA/qwen-runtime"
if not (RUNTIME / "diffsynth/pipelines/qwen_image_21.py").is_file():
    raise RuntimeError("Download and extract models/Garments2Look-LoRA/qwen-runtime.zip as described in README.md before training.")
sys.path.insert(0, str(RUNTIME))

import torch, os, argparse, accelerate
from diffsynth.core import UnifiedDataset
from diffsynth.pipelines.qwen_image import QwenImagePipeline
from diffsynth.pipelines.qwen_image_21 import QwenImage21Pipeline, ModelConfig
from diffsynth.diffusion import *
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class QwenImageTrainingModule(DiffusionTrainingModule):
    def __init__(
        self,
        model_paths=None, model_id_with_origin_paths=None,
        processor_path=None, tokenizer_path=None, model_version="2509", zero_cond_t=False,
        trainable_models=None,
        lora_base_model=None, lora_target_modules="", lora_rank=32, lora_checkpoint=None,
        preset_lora_path=None, preset_lora_model=None,
        use_gradient_checkpointing=True,
        use_gradient_checkpointing_offload=False,
        extra_inputs=None,
        fp8_models=None,
        offload_models=None,
        resume_from_checkpoint=None, remove_prefix_in_ckpt=None,
        device="cpu",
        task="sft",
    ):
        super().__init__()
        # Load models
        model_configs = self.parse_model_configs(model_paths, model_id_with_origin_paths, fp8_models=fp8_models, offload_models=offload_models, device=device)
        self.model_version = model_version
        self.zero_cond_t = zero_cond_t
        if model_version == "2.1":
            processor_config = ModelConfig(model_id="Qwen/Qwen-Image-2.1", origin_file_pattern="processor/") if processor_path is None else ModelConfig(processor_path)
            self.pipe = QwenImage21Pipeline.from_pretrained(torch_dtype=torch.bfloat16, device=device, model_configs=model_configs, processor_config=processor_config)
        else:
            tokenizer_config = ModelConfig(model_id="Qwen/Qwen-Image", origin_file_pattern="tokenizer/") if tokenizer_path is None else ModelConfig(tokenizer_path)
            processor_config = ModelConfig(model_id="Qwen/Qwen-Image-Edit", origin_file_pattern="processor/") if processor_path is None else ModelConfig(processor_path)
            self.pipe = QwenImagePipeline.from_pretrained(torch_dtype=torch.bfloat16, device=device, model_configs=model_configs, tokenizer_config=tokenizer_config, processor_config=processor_config)
        self.pipe = self.split_pipeline_units(task, self.pipe, trainable_models, lora_base_model)
        self.resume_from_checkpoint(resume_from_checkpoint, remove_prefix_in_ckpt)

        # Training mode
        self.switch_pipe_to_training_mode(
            self.pipe, trainable_models,
            lora_base_model, lora_target_modules, lora_rank, lora_checkpoint,
            preset_lora_path, preset_lora_model,
            task=task,
        )

        # Other configs
        self.use_gradient_checkpointing = use_gradient_checkpointing
        self.use_gradient_checkpointing_offload = use_gradient_checkpointing_offload
        self.extra_inputs = extra_inputs.split(",") if extra_inputs is not None else []
        self.fp8_models = fp8_models
        self.task = task
        self.task_to_loss = {
            "sft:data_process": lambda pipe, *args: args,
            "sft": lambda pipe, inputs_shared, inputs_posi, inputs_nega: FlowMatchSFTLoss(pipe, **inputs_shared, **inputs_posi),
            "sft:train": lambda pipe, inputs_shared, inputs_posi, inputs_nega: FlowMatchSFTLoss(pipe, **inputs_shared, **inputs_posi),
        }

    def get_pipeline_inputs(self, data):
        inputs_posi = {"prompt": data["prompt"]}
        inputs_nega = {"negative_prompt": ""}
        inputs_shared = {
            # Please do not modify the following parameters
            # unless you clearly know what this will cause.
            "cfg_scale": 1,
            "use_flex_attention": True,
            "use_kv_cache": False,
            "rand_device": self.pipe.device,
            "use_gradient_checkpointing": self.use_gradient_checkpointing,
            "use_gradient_checkpointing_offload": self.use_gradient_checkpointing_offload,
            "tiled": False,
            "tile_size": 256,
            "tile_stride": 192,
            "input_image": data["image"],
            "height": data["image"].size[1],
            "width": data["image"].size[0],
        }
        if self.model_version == "2509":
            for key in ("use_flex_attention", "use_kv_cache", "tiled", "tile_size", "tile_stride"):
                inputs_shared.pop(key)
            inputs_shared.update(edit_image_auto_resize=True, zero_cond_t=self.zero_cond_t)
        inputs_shared = self.parse_extra_inputs(data, self.extra_inputs, inputs_shared)
        return inputs_shared, inputs_posi, inputs_nega

    def forward(self, data, inputs=None):
        if inputs is None: inputs = self.get_pipeline_inputs(data)
        inputs = self.transfer_data_to_device(inputs, self.pipe.device, self.pipe.torch_dtype)
        for unit in self.pipe.units:
            inputs = self.pipe.unit_runner(unit, self.pipe, *inputs)
        loss = self.task_to_loss[self.task](self.pipe, *inputs)
        return loss


class TrainingLogger(ModelLogger):
    def on_step_end(self, accelerator, model, save_steps=None, loss=None, **kwargs):
        if not torch.isfinite(loss.detach()).all():
            raise RuntimeError("Training loss is not finite")
        super().on_step_end(accelerator, model, save_steps=save_steps, loss=loss, **kwargs)
        if accelerator.is_main_process:
            os.makedirs(self.output_path, exist_ok=True)
            with open(os.path.join(self.output_path, "training.jsonl"), "a") as f:
                f.write(json.dumps({"step": self.num_steps, "loss": float(loss.detach().float().item())}) + "\n")


def qwen_image_parser():
    parser = argparse.ArgumentParser(description="Garments2Look Qwen 2509 / 2.1 LoRA training (inpainting / editing).")
    parser.add_argument("--seed", type=int, default=None, help="Optional training seed. The released 2.1 runs did not set a seed.")
    parser.add_argument("--model_version", choices=["2509", "2.1"], default="2509")
    parser.add_argument("--tokenizer_path", default=None)
    parser.add_argument("--zero_cond_t", action="store_true")
    parser = add_general_config(parser)
    parser = add_image_size_config(parser)
    parser.add_argument("--model_dir", type=Path, default=ROOT / "models/Qwen-Image-2.1", help="Local base-model directory.")
    parser.add_argument("--processor_path", type=str, default=None, help="Path to the processor. If provided, the processor will be used instead of the remote one.")
    parser.add_argument("--initialize_model_on_cpu", default=False, action="store_true", help="Whether to initialize models on CPU.")
    return parser


if __name__ == "__main__":
    parser = qwen_image_parser()
    args = parser.parse_args()
    if args.seed is not None:
        accelerate.utils.set_seed(args.seed)
    if args.model_version == "2.1" and args.model_paths is None and args.model_id_with_origin_paths is None:
        groups = []
        for pattern in ("transformer/diffusion_pytorch_model*.safetensors", "text_encoder/model*.safetensors", "vae/diffusion_pytorch_model*.safetensors"):
            files = sorted(args.model_dir.glob(pattern))
            if not files:
                raise FileNotFoundError(args.model_dir / pattern)
            groups.append([str(p) for p in files] if len(files) > 1 else str(files[0]))
        args.model_paths = json.dumps(groups)
    if args.model_version == "2.1" and args.processor_path is None:
        args.processor_path = str(args.model_dir / "processor")
    accelerator = accelerate.Accelerator(
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        kwargs_handlers=[accelerate.DistributedDataParallelKwargs(find_unused_parameters=args.find_unused_parameters)],
    )
    dataset = UnifiedDataset(
        base_path=args.dataset_base_path,
        metadata_path=args.dataset_metadata_path,
        repeat=args.dataset_repeat,
        data_file_keys=args.data_file_keys.split(","),
        main_data_operator=UnifiedDataset.default_image_operator(
            base_path=args.dataset_base_path,
            max_pixels=args.max_pixels,
            height=args.height,
            width=args.width,
            height_division_factor=32 if args.model_version == "2.1" else 16,
            width_division_factor=32 if args.model_version == "2.1" else 16,
            convert_RGB=args.model_version == "2509",
            convert_RGBA=args.model_version == "2.1",
        ),
    )
    model = QwenImageTrainingModule(
        model_version=args.model_version, tokenizer_path=args.tokenizer_path, zero_cond_t=args.zero_cond_t,
        model_paths=args.model_paths,
        model_id_with_origin_paths=args.model_id_with_origin_paths,
        processor_path=args.processor_path,
        trainable_models=args.trainable_models,
        lora_base_model=args.lora_base_model,
        lora_target_modules=args.lora_target_modules,
        lora_rank=args.lora_rank,
        lora_checkpoint=args.lora_checkpoint,
        preset_lora_path=args.preset_lora_path,
        preset_lora_model=args.preset_lora_model,
        use_gradient_checkpointing=args.use_gradient_checkpointing,
        use_gradient_checkpointing_offload=args.use_gradient_checkpointing_offload,
        extra_inputs=args.extra_inputs,
        fp8_models=args.fp8_models,
        offload_models=args.offload_models,
        resume_from_checkpoint=args.resume_from_checkpoint,
        remove_prefix_in_ckpt=args.remove_prefix_in_ckpt,
        task=args.task,
        device="cpu" if (args.initialize_model_on_cpu or args.enable_model_cpu_offload) else accelerator.device,
    )
    model_logger = (ModelLogger if args.model_version == "2.1" else TrainingLogger)(
        args.output_path,
        remove_prefix_in_ckpt=args.remove_prefix_in_ckpt,
        enable_tensorboard_log=args.enable_tensorboard_log,
        enable_swanlab_log=args.enable_swanlab_log,
        swanlab_project=args.swanlab_project,
        enable_wandb_log=args.enable_wandb_log,
        wandb_project=args.wandb_project,
        enable_csv_log=args.enable_csv_log,
    )
    launcher_map = {
        "sft:data_process": launch_data_process_task,
        "sft": launch_training_task,
        "sft:train": launch_training_task,
    }
    launcher_map[args.task](accelerator, dataset, model, model_logger, args=args)
