# Garments2Look [CVPR 2026]

> **Paper**: Garments2Look: A Multi-Reference Dataset for High-Fidelity Outfit-Level Virtual Try-On with Clothing and Accessories
>
> **Authors**: [Junyao Hu](https://junyaohu.github.io/), [Zhongwei Cheng](https://scholar.google.com/citations?user=ayN-dVwAAAAJ), [Waikeung Wong](https://research.polyu.edu.hk/en/persons/wai-keung-wong-2/), [Xingxing Zou](https://scholar.google.com/citations?user=UhnQA3UAAAAJ)

- Paper: [arXiv](https://arxiv.org/abs/2603.14153), [CVPR](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Garments2Look_A_Multi-Reference_Dataset_for_High-Fidelity_Outfit-Level_Virtual_Try-On_with_CVPR_2026_paper.html), [中译版](./docs/Garments2Look-Chinese.pdf)
- [Project Page](https://artmesciencelab.github.io/Garments2Look/)
- [Poster](./docs/poster.pdf)
- [Dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look)
- [LoRA Models](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA)
- [Comparison Results on Test Set](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look-Test-Set-Results)

https://github.com/user-attachments/assets/a2926af9-8ab2-435b-9afc-5b2587458efa


## News and updates

- **[2026-10-11]** Released final [Qwen-Image-2.1 inpainting and editing LoRAs](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA), with both-model inference and paired seed-0 examples.

- **[2026-10-04]** Updated the [dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look) to 98,012 outfit records, with five annotation types, refined and dilated v3 masks, OOTD collages, and editing source images.
- **[2026-10-04]** Released [Qwen-Image-Edit-2509 LoRAs](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA) for inpainting and editing.

- **[2026-04-09]** Garments2Look was accepted to **CVPR 2026**.
- **[2026-03-17]** Released the [Garments2Look dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look), including all image data and inputs for the inpainting task setting.
- **[2026-03-14]** Submitted the first version of our paper to [arXiv](https://arxiv.org/abs/2603.14153).

## TODO

- [x] Release Qwen 2509 LoRAs for inpainting and editing.
- [x] Add dataset preparation, training, inference, and examples.
- [x] Release editing-task inputs, v1.1 outfit annotations, and improved v3 masks.
- [x] Train and open-source Qwen Image 2.1 LoRAs.

## Overview

Virtual try-on (VTON) has advanced single-garment visualization, yet real-world fashion centers on full outfits with multiple garments, accessories, fine-grained categories, layering, and diverse styling, remaining beyond current VTON systems. Existing datasets are category-limited and lack outfit diversity. We introduce Garments2Look, the first large-scale multimodal dataset for outfit-level VTON, comprising approximately 80K many-garments-to-one-look pairs in the paper, expanded to 98,012 indexed outfit records in the current dataset across 40 major categories and 300+ fine-grained subcategories. Each pair includes an outfit with 3-12 reference garment images (4.48 items per outfit on average), a model image wearing the outfit, and detailed item and try-on textual annotations. To balance authenticity and diversity, we propose a synthesis pipeline. It involves heuristically constructing outfit lists before generating try-on results, with the entire process subjected to strict automated filtering and human validation to ensure data quality. To probe task difficulty, we adapt SOTA VTON methods and general-purpose image editing models to establish baselines. Results show current methods struggle to try on complete outfits seamlessly and to infer correct layering and styling, leading to misalignment and artifacts.

![Dataset Comparison](./docs/dataset-compare.jpg)

**Dataset comparison.** Garments2Look targets complete outfits with multiple clothing items and accessories, including annotations of layering and styling.

## Dataset construction

![Pipeline](./docs/pipeline.jpg)

**Overview of Garments2Look construction process.** Our dataset follows four steps: (1) Data Collection: obtaining real-world clothing items and their outfit suggestions from different sources; (2) Data Synthesis: enriching the dataset content and diversity by generating new outfit lists and look images; (3) Data Filtering: ensuring visual consistency and data quality, including annotations of garment images, outfit lists and look images; and (4) Data Evaluation: verifying the data quality, designing new metrics for outfit-level VTON task, and testing SOTA models.

![Data structure](./docs/examples.jpg)

**Sample outfits and annotations.** Each sample pairs multiple reference items with a look image and annotations describing the outfit, layering, and styling.

<a id="qwen-image-edit-2509-lora"></a>

## Qwen LoRA models

## Checkpoints

| Base model | Task | File | Training |
| --- | --- | --- | --- |
| Qwen-Image-Edit-2509 | Inpainting | `Qwen-Image-Edit-2509-LoRA-2-refer-20k-inpainting-epoch-1.safetensors` | 20,000 samples; 2 completed epochs; rank 32 |
| Qwen-Image-Edit-2509 | Editing | `Qwen-Image-Edit-2509-LoRA-2-refer-20k-editing-epoch-1.safetensors` | 20,000 samples; 2 completed epochs; rank 32 |
| Qwen-Image-2.1 | Inpainting | `Qwen-Image-2.1-LoRA-2-refer-97068-inpainting-epoch-0.safetensors` | 97,068 samples; 1 completed epoch; final step 48,534; rank 32 |
| Qwen-Image-2.1 | Editing | `Qwen-Image-2.1-LoRA-2-refer-97068-editing-epoch-0.safetensors` | 97,068 samples; 1 completed epoch; final step 48,534; rank 32 |

Epoch numbers are zero-indexed: `epoch-1` means two completed epochs, and `epoch-0` means one completed epoch. Both 2.1 files are the final **step-48534** checkpoints, not step-48000. These are adapters, not full models. Use the matching base model and task. File checksums and training metadata are in [HF manifest.json](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA/blob/main/manifest.json).

## Installation and download

Tested with Python 3.10, PyTorch 2.7.1 / CUDA 12.8, Transformers 5.16.1, and H200 GPUs. Run commands from the repository root. Clone the code repository first:

```bash
git clone https://github.com/ArtmeScienceLab/Garments2Look.git
cd Garments2Look
``` Download only the base model you intend to use.

```bash
conda create -n g2l-lora python=3.10 -y
conda activate g2l-lora
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install huggingface_hub
hf download ArtmeScienceLab/Garments2Look-LoRA --local-dir models/Garments2Look-LoRA
python -m zipfile -e models/Garments2Look-LoRA/qwen-runtime.zip models/Garments2Look-LoRA
python -m pip install -e models/Garments2Look-LoRA/qwen-runtime
python -m pip install transformers==5.16.1

hf download Qwen/Qwen-Image-Edit-2509 --local-dir models/Qwen-Image-Edit-2509
hf download Qwen/Qwen-Image-2.1 --local-dir models/Qwen-Image-2.1
```

The repository inference script imports the extracted runtime. Adapters use the DiffSynth format; compatibility with other LoRA loaders has not been verified. Set `CUDA_VISIBLE_DEVICES` to choose a GPU.

## Inpainting inference

### Qwen-Image-Edit-2509

```bash
python scripts/inference/inference.py --model-version 2509 --task inpainting \
  --model-dir models/Qwen-Image-Edit-2509 \
  --lora models/Garments2Look-LoRA/Qwen-Image-Edit-2509-LoRA-2-refer-20k-inpainting-epoch-1.safetensors \
  --origin examples/qwen2509/input-inpainting.png \
  --ootd examples/qwen2509/ootd.png \
  --prompt-file examples/qwen2509/prompt-inpainting.txt \
  --output output/qwen2509-inpainting.png --seed 0 --steps 40 --cfg-scale 4
```

### Qwen-Image-2.1

```bash
python scripts/inference/inference.py --model-version 2.1 --task inpainting \
  --model-dir models/Qwen-Image-2.1 \
  --lora models/Garments2Look-LoRA/Qwen-Image-2.1-LoRA-2-refer-97068-inpainting-epoch-0.safetensors \
  --origin examples/qwen21/input-inpainting.png \
  --ootd examples/qwen21/ootd.png \
  --prompt-file examples/qwen21/prompt-inpainting.txt \
  --output output/qwen21-inpainting.png --seed 0 --steps 40 --cfg-scale 1
```

## Editing inference

### Qwen-Image-Edit-2509

```bash
python scripts/inference/inference.py --model-version 2509 --task editing \
  --model-dir models/Qwen-Image-Edit-2509 \
  --lora models/Garments2Look-LoRA/Qwen-Image-Edit-2509-LoRA-2-refer-20k-editing-epoch-1.safetensors \
  --origin examples/qwen2509/input-editing.png \
  --ootd examples/qwen2509/ootd.png \
  --prompt-file examples/qwen2509/prompt-editing.txt \
  --output output/qwen2509-editing.png --seed 0 --steps 40 --cfg-scale 4
```

### Qwen-Image-2.1

```bash
python scripts/inference/inference.py --model-version 2.1 --task editing \
  --model-dir models/Qwen-Image-2.1 \
  --lora models/Garments2Look-LoRA/Qwen-Image-2.1-LoRA-2-refer-97068-editing-epoch-0.safetensors \
  --origin examples/qwen21/input-editing.png \
  --ootd examples/qwen21/ootd.png \
  --prompt-file examples/qwen21/prompt-editing.txt \
  --output output/qwen21-editing.png --seed 0 --steps 40 --cfg-scale 1
```

Default seed is **0**, with 40 steps. If CFG is omitted, the script uses 4 for 2509 and 1 for 2.1. Images use a 1,048,576-pixel budget, aligned to multiples of 16 for 2509 and 32 for 2.1. Each invocation saves its PNG and a JSON parameter record. For custom outfits, replace Figure 1, the collage, and the full prompt.

## Paired example: P00958796_b1

This five-item test outfit includes a top, jacket, shorts, sandals, and bag. Styling specifies a **tucked-in top** and an **unbuttoned jacket**; layering is **top → jacket**. Both task prompts are supplied in the example folders.

### Qwen-Image-Edit-2509 LoRA

![2509 inpainting and editing, seed 0](./examples/qwen2509/comparison.jpg)

### Qwen-Image-2.1 LoRA

![2.1 inpainting and editing, final step 48534, seed 0](./examples/qwen21/comparison.jpg)

Columns: OOTD, inpainting input, inpainting output, editing input, editing output. Full task prompts are printed below each figure. Both models use seed 0 and 40 steps, with CFG 4 for 2509 and CFG 1 for 2.1. The 2.1 images use the final adapters released above.

**Full prompt (both tasks):**

> Keep the woman's identity, pose, background in Figure 1 unchanged, wearing the outfit in Figure 2, include (1) a top (tucked-in), (2) a jacket (unbuttoned), (3) shorts, (4) sandals, (5) a bag. Layering Order: (1) -> (2).

This example was selected after comparing six candidate outfits at fixed seed 0, four outputs per candidate. It illustrates a selected successful case, not aggregate test performance. The two base models were trained on different data counts and epoch counts. Bag shape, garment hems, and pose may still differ. Selection provenance is in [examples/selection.json](./examples/manifest.json); each output has a parameter JSON, and target images are included.

## Training details

| Setting | 2509 | 2.1 |
| --- | --- | --- |
| Training examples | 20,000 | Full 97,068 training split |
| Completed epochs | 2 | 1 |
| LoRA rank | 32 | 32 |
| Learning rate | 1e-4 | 1e-4 |
| Pixel budget | 1,048,576 | 1,048,576 |
| Precision | BF16 | BF16 |
| Gradient checkpointing | Enabled | Enabled |
| Final step | Epoch-based checkpoint | 48,534 |

The 2.1 runs used two H200 GPUs and global batch size 2. Training took approximately 58h36m (inpainting) and 58h50m (editing). These adapters are later releases than the paper's rebuttal-stage models; the selected examples do not establish aggregate improvements over those models.

For dataset preparation and the public 2509 training workflow, see the code repository. The HF runtime and this repository's inference script support both models. The existing training launcher in this public repository targets 2509; a complete 2.1 training launcher is not included.


## Dataset preparation and 2509 training

### Download training dataset

**Skip this section for inference with the bundled examples or your own prepared input images.** Full dataset downloads are needed for training and dataset analysis.

For training or dataset analysis, download the annotations and image archives from [Hugging Face](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look/tree/main):

```bash
python -m pip install -U huggingface_hub
hf download ArtmeScienceLab/Garments2Look --repo-type dataset \
  --local-dir /path/to/Garments2Look-data
```

The current release contains **56 independent `.tar.gz` archives**, approximately **437.54 GB (407.49 GiB)** compressed, plus JSON annotations (approximately **438.1 GB** in total). Each archive includes paths beginning with `mytheresa/` or `polyvore/`. Extract every archive into the dataset root:

```bash
cd /path/to/Garments2Look-data
sha256sum -c SHA256SUMS
find mytheresa polyvore -type f -name '*.tar.gz' -print0 |
  while IFS= read -r -d '' archive; do
    tar -xzf "$archive" -C .
  done
```

Each shard can be extracted independently. Keep the original subset layout:

```text
Garments2Look-data/
├── Garments2Look.py
├── mytheresa_image_v1.0_2512.json
├── mytheresa_outfit_v1.0_2512.json
├── mytheresa_outfit_v1.1_2512.json
├── polyvore_image_v1.0_2512.json
├── polyvore_outfit_v1.0_2512.json
├── polyvore_outfit_v1.1_2512.json
├── mytheresa/
│   ├── images/
│   ├── looks-resized/
│   ├── ootd/
│   ├── edited/banana/
│   └── annotations/  # ATR, DensePose, DWPose, LIP, and mask-v3-look-resized
└── polyvore/         # Same asset layout
```

The v1.0 JSON index has 80,041 records. The recommended v1.1 index has **98,012 records: 97,068 train and 944 test**, adding 17,971 training records. See the [dataset card](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look#annotations-and-splits) for counts by source, mask construction, and full asset details.

### Prepare training data

Use the released v1.1 outfit annotations and retain their `section` assignments. Inpainting inputs replace the foreground of `annotations/mask-v3-look-resized/<gender>/<id>.png` with gray (128). The refined v3 masks improve coverage and include dilation; regenerate agnostic caches when changing masks. The dataset release includes ATR, DensePose, DWPose, LIP, and v3 mask annotations.

Editing source images are available at `<subset>/edited/banana/<id>.png`, and OOTD collages are included at `<subset>/ootd/<gender>/<id>.png`. Missing OOTD collages can be generated from reference item images in prompt order. The bundled example is a paired test sample for checking inference.

```bash
python scripts/data_gen/generate_2-refer.py --task inpainting --section train \
  --dataset-root /path/to/Garments2Look-data --num-samples 20000 \
  --num-workers 4 --seed 123 --output data/metadata/train-inpainting.json

# Requires editing source images.
python scripts/data_gen/generate_2-refer.py --task editing --section train \
  --dataset-root /path/to/Garments2Look-data --num-samples 20000 \
  --num-workers 4 --seed 123 --output data/metadata/train-editing.json
```

Metadata is a JSON list. Each record contains a target `image`, full `prompt`, and two `edit_image` paths in Figure 1 / Figure 2 order. Paths may be absolute or relative to `DATASET_ROOT`; generated metadata uses local paths, so regenerate it when moving data to another machine. Check the reported written/skipped counts before training.

```json
[
  {
    "image": "path/to/target-look.png",
    "prompt": "Keep the person's identity, pose, background in Figure 1 unchanged, wearing the outfit in Figure 2...",
    "edit_image": ["path/to/source-person.png", "path/to/ootd.png"]
  }
]
```

### Training

Select the task and its metadata. The defaults match the original LoRA recipe: rank 32, learning rate 1e-4, two epochs, gradient checkpointing, and a 1,048,576-pixel budget.

```bash
export MODEL_DIR="$PWD/models/Qwen-Image-Edit-2509"
export DATASET_ROOT=/path/to/Garments2Look-data
export TASK=inpainting
export METADATA="$PWD/data/metadata/train-inpainting.json"
export OUTPUT_DIR="$PWD/models/train/$TASK"
NPROC=1 SEED=123 bash scripts/train/train_lora.sh

# Editing training (requires editing-task inputs).
export TASK=editing
export METADATA="$PWD/data/metadata/train-editing.json"
export OUTPUT_DIR="$PWD/models/train/$TASK"
NPROC=1 SEED=123 bash scripts/train/train_lora.sh

# Optional: train the selected task on two GPUs.
CUDA_VISIBLE_DEVICES=0,1 NPROC=2 SEED=123 bash scripts/train/train_lora.sh
```

Checkpoint filenames are zero-indexed: `epoch-0.safetensors` is saved after the first epoch and `epoch-1.safetensors` after the second. Losses are written to `training.jsonl`. The example runs use second-epoch checkpoints trained on 20K samples, not newly trained smoke-test weights. Both task-specific adapters are available from [Hugging Face](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA); use their downloaded paths with `--lora`.


## License

The Garments2Look dataset is released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), permitting commercial use, modification, and redistribution under its terms. Retain applicable copyright, attribution, and license notices, including those accompanying third-party materials.

The code is licensed under [Apache 2.0](./LICENSE) and includes an adapted [DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio) implementation; see [NOTICE](./NOTICE). See the [model repository](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA) for LoRA weight licensing information; an explicit adapter license is not yet specified.

## Citation

If you use our dataset or models in your research, please consider citing our paper:

```bibtex
@inproceedings{cvpr2026garments2look,
    title={Garments2Look: A Multi-Reference Dataset for High-Fidelity Outfit-Level Virtual Try-On with Clothing and Accessories},
    author={Hu, Junyao and Cheng, Zhongwei and Wong, Waikeung and Zou, Xingxing},
    booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
    year={2026}
}
```
