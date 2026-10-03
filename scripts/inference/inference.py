"""Two-reference Qwen-Image-Edit-2509 inference with a task-specific LoRA."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task", required=True, choices=["inpainting", "editing"])
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--lora", type=Path, required=True)
    p.add_argument("--origin", type=Path, required=True, help="Masked person for inpainting, source person for editing")
    p.add_argument("--ootd", type=Path, required=True)
    p.add_argument("--prompt", help="Full prompt; mutually exclusive with --prompt-file")
    p.add_argument("--prompt-file", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--cfg-scale", type=float, default=4.0)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    if bool(args.prompt) == bool(args.prompt_file):
        p.error("Specify exactly one of --prompt or --prompt-file")
    if args.steps <= 0:
        p.error("--steps must be positive")
    return args


def main():
    args = parse_args()
    for path in [args.model_dir, args.lora, args.origin, args.ootd]:
        if not path.exists():
            raise FileNotFoundError(path)
    prompt = args.prompt if args.prompt else args.prompt_file.read_text().strip()
    if not prompt.strip():
        raise ValueError("Prompt is empty")
    # Import after argument parsing so --help does not load model dependencies.
    import torch
    from PIL import Image
    from diffsynth.pipelines.qwen_image import QwenImagePipeline, ModelConfig
    from diffsynth.core.data.operators import ImageCropAndResize
    patterns = ["transformer/diffusion_pytorch_model*.safetensors", "text_encoder/model*.safetensors", "vae/diffusion_pytorch_model.safetensors"]
    configs = []
    for pattern in patterns:
        paths = sorted(args.model_dir.glob(pattern))
        if not paths:
            raise FileNotFoundError(f"No weights matching {args.model_dir / pattern}")
        configs.append(ModelConfig(path=[str(p) for p in paths] if len(paths) > 1 else str(paths[0])))
    pipe = QwenImagePipeline.from_pretrained(
        torch_dtype=torch.bfloat16, device=args.device,
        model_configs=configs, tokenizer_config=None,
        processor_config=ModelConfig(path=str(args.model_dir / "processor")),
    )
    pipe.load_lora(pipe.dit, str(args.lora))
    origin = Image.open(args.origin).convert("RGB")
    ootd = Image.open(args.ootd).convert("RGB")
    # Match training's 16-pixel alignment and pixel budget.
    origin = ImageCropAndResize(max_pixels=1048576, height_division_factor=16, width_division_factor=16)(origin)
    image = pipe(prompt, edit_image=[origin, ootd], seed=args.seed,
                 num_inference_steps=args.steps, cfg_scale=args.cfg_scale,
                 height=origin.height, width=origin.width)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    run = {"task": args.task, "prompt": prompt, "seed": args.seed, "steps": args.steps,
           "cfg_scale": args.cfg_scale, "model_dir": str(args.model_dir.resolve()),
           "lora": str(args.lora.resolve()), "origin": str(args.origin.resolve()),
           "ootd": str(args.ootd.resolve()), "output": str(args.output.resolve()),
           "width": origin.width, "height": origin.height}
    args.output.with_suffix(".json").write_text(json.dumps(run, indent=2))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
