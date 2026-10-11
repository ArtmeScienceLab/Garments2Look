#!/usr/bin/env bash
#SBATCH --job-name=qwen21-editing
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:2
#SBATCH --mem=120G
#SBATCH --time=5-00:00:00
#SBATCH --output=qwen21-editing-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
# Activate the installed training environment before sbatch; it is inherited.
# Adjust partition, GPU type and resource requests for your cluster.
bash scripts/train/train_qwen21_lora-2-refer-editing.sh "$@"
