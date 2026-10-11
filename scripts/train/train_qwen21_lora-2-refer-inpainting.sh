#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export MASTER_PORT="${MASTER_PORT:-$((29500 + ${SLURM_JOB_ID:-$$} % 1000))}"
export DIFFSYNTH_SKIP_DOWNLOAD=true
export TORCHINDUCTOR_COMPILE_THREADS="${TORCHINDUCTOR_COMPILE_THREADS:-1}"
NPROC="${NPROC:-2}"
DISTRIBUTED=()
if (( NPROC > 1 )); then DISTRIBUTED+=(--multi_gpu); fi
accelerate launch --num_processes="$NPROC" "${DISTRIBUTED[@]}" --mixed_precision=bf16 --main_process_port "$MASTER_PORT" scripts/train/train.py --model_version 2.1 \
  --model_dir "${MODEL_DIR:?Set MODEL_DIR to Qwen-Image-2.1}" \
  --dataset_base_path "${DATASET_ROOT:?Set DATASET_ROOT}" \
  --dataset_metadata_path "${METADATA_PATH:-data/metadata/garments2look-2-refer-inpainting-for-qwen21-train-97068.json}" \
  --data_file_keys "image,edit_image" \
  --extra_inputs "edit_image" \
  --max_pixels "${MAX_PIXELS:-1048576}" \
  --dataset_repeat 1 \
  --learning_rate 1e-4 \
  --num_epochs "${NUM_EPOCHS:-1}" \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "${OUTPUT_PATH:-models/train/qwen21-inpainting}" \
  --lora_base_model "dit" \
  --lora_target_modules "to_q,to_k,to_v,to_out.0,img_mlp.proj,img_mlp.gate_layer,img_mlp.out,modulation.1" \
  --lora_rank 32 \
  --use_gradient_checkpointing \
  --dataset_num_workers "${NUM_WORKERS:-8}" \
  --find_unused_parameters \
  --enable_csv_log \
  --save_steps 1000 \
  "$@"
