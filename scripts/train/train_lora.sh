#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
: "${MODEL_DIR:?Set MODEL_DIR to Qwen-Image-Edit-2509}"
: "${DATASET_ROOT:?Set DATASET_ROOT}"
: "${METADATA:?Set METADATA to the task-specific training JSON}"
TASK="${TASK:-inpainting}"
case "$TASK" in inpainting|editing) ;; *) echo "TASK must be inpainting or editing" >&2; exit 1;; esac
MODEL_PATHS=$(python -c 'import glob,json,os; r=os.environ["MODEL_DIR"]; patterns=["transformer/diffusion_pytorch_model*.safetensors","text_encoder/model*.safetensors","vae/diffusion_pytorch_model.safetensors"]; paths=[sorted(glob.glob(os.path.join(r,p))) for p in patterns]; assert all(paths), "Missing base model weights"; print(json.dumps([v if len(v)>1 else v[0] for v in paths]))')
NPROC="${NPROC:-1}"
DISTRIBUTED=()
if (( NPROC > 1 )); then DISTRIBUTED+=(--multi_gpu); fi
accelerate launch --num_processes "$NPROC" "${DISTRIBUTED[@]}" \
  --main_process_port "${MASTER_PORT:-29500}" scripts/train/train.py \
  --dataset_base_path "$DATASET_ROOT" --dataset_metadata_path "$METADATA" \
  --data_file_keys "image,edit_image" --extra_inputs "edit_image" \
  --max_pixels 1048576 --dataset_repeat 1 --model_paths "$MODEL_PATHS" \
  --processor_path "$MODEL_DIR/processor" \
  --learning_rate "${LEARNING_RATE:-1e-4}" --num_epochs "${EPOCHS:-2}" \
  --remove_prefix_in_ckpt "pipe.dit." --output_path "${OUTPUT_DIR:-models/train/$TASK}" \
  --lora_base_model dit \
  --lora_target_modules "to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1" \
  --lora_rank 32 --use_gradient_checkpointing --dataset_num_workers "${NUM_WORKERS:-4}" \
  --find_unused_parameters --seed "${SEED:-123}" "$@"
