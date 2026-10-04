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

- **[2026-10-04]** Updated the [dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look) to 98,012 outfit records, with five annotation types, refined and dilated v3 masks, OOTD collages, and editing source images.
- **[2026-10-04]** Released [Qwen-Image-Edit-2509 LoRAs](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA) for inpainting and editing.

- **[2026-04-09]** Garments2Look was accepted to **CVPR 2026**.
- **[2026-03-17]** Released the [Garments2Look dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look), including all image data and inputs for the inpainting task setting.
- **[2026-03-14]** Submitted the first version of our paper to [arXiv](https://arxiv.org/abs/2603.14153).

## TODO

- [x] Release [Qwen 2509 LoRAs](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA) for inpainting and editing.
- [x] Add dataset preparation, training, inference, and examples.
- [x] Release editing-task inputs, v1.1 outfit annotations, and improved v3 masks.
- [ ] Train and open-source Qwen Image 2.1 LoRAs.

## Overview

Virtual try-on (VTON) has advanced single-garment visualization, yet real-world fashion centers on full outfits with multiple garments, accessories, fine-grained categories, layering, and diverse styling, remaining beyond current VTON systems. Existing datasets are category-limited and lack outfit diversity. We introduce Garments2Look, the first large-scale multimodal dataset for outfit-level VTON, comprising approximately 80K many-garments-to-one-look pairs in the paper, expanded to 98,012 indexed outfit records in the current dataset across 40 major categories and 300+ fine-grained subcategories. Each pair includes an outfit with 3-12 reference garment images (4.48 items per outfit on average), a model image wearing the outfit, and detailed item and try-on textual annotations. To balance authenticity and diversity, we propose a synthesis pipeline. It involves heuristically constructing outfit lists before generating try-on results, with the entire process subjected to strict automated filtering and human validation to ensure data quality. To probe task difficulty, we adapt SOTA VTON methods and general-purpose image editing models to establish baselines. Results show current methods struggle to try on complete outfits seamlessly and to infer correct layering and styling, leading to misalignment and artifacts.

![Dataset Comparison](./docs/dataset-compare.jpg)

**Dataset comparison.** Garments2Look targets complete outfits with multiple clothing items and accessories, including annotations of layering and styling.

## Dataset construction

![Pipeline](./docs/pipeline.jpg)

**Overview of Garments2Look construction process.** Our dataset follows four steps: (1) Data Collection: obtaining real-world clothing items and their outfit suggestions from different sources; (2) Data Synthesis: enriching the dataset content and diversity by generating new outfit lists and look images; (3) Data Filtering: ensuring visual consistency and data quality, including annotations of garment images, outfit lists and look images; and (4) Data Evaluation: verifying the data quality, designing new metrics for outfit-level VTON task, and testing SOTA models.

![Data structure](./docs/examples.jpg)

**Sample outfits and annotations.** Each sample pairs multiple reference items with a look image and annotations describing the outfit, layering, and styling.

## Qwen-Image-Edit-2509 LoRA

For inference, download the base model and released LoRAs below, then use the bundled [`examples/`](./examples/) inputs or your own prepared images. You do not need the full dataset.

Both tasks use two reference images: **Figure 1** is the masked person (inpainting) or source person (editing); **Figure 2** is an OOTD collage of the target items. Use a separate LoRA checkpoint for each task.

### Installation

```bash
git clone https://github.com/ArtmeScienceLab/Garments2Look.git
cd Garments2Look
```

Run commands from the repository root. The tested environment uses Python 3.10, PyTorch 2.7.1 with CUDA 12.8, and an NVIDIA H200:

```bash
conda create -n g2l-lora python=3.10 -y
conda activate g2l-lora
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
hf download Qwen/Qwen-Image-Edit-2509 --local-dir models/Qwen-Image-Edit-2509
hf download ArtmeScienceLab/Garments2Look-LoRA --local-dir models/Garments2Look-LoRA
```

The repository vendors the DiffSynth implementation used by the original experiments. No Slurm installation is required. Model weights, full data, training logs, and local server configuration are excluded from Git.

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

### Example files

The self-contained [`examples/`](./examples/) folder includes the original inputs, target outfit collage, full prompts, and generated outputs:

```text
examples/
├── input-inpainting.png     # Original masked person input
├── input-editing.png        # Original source person input
├── ootd.png                 # Target outfit reference collage
├── target.png               # Dataset target look (not used as inference input)
├── prompt-inpainting.txt
├── prompt-editing.txt
├── output-inpainting.png    # Seed 123
├── output-editing.png       # Seed 123
├── comparison.jpg / .png    # Five columns and two full-width prompt lines
└── manifest.json / validation.json
```

Only the two input images (`input-<task>.png` and `ootd.png`) and the corresponding prompt file are needed for inference; no full dataset download is required for these examples. Supply the base model and the task-specific LoRA checkpoint separately.

### Inference

```bash
python scripts/inference/inference.py --task inpainting \
  --model-dir models/Qwen-Image-Edit-2509 \
  --lora models/Garments2Look-LoRA/Qwen-Image-Edit-2509-LoRA-2-refer-20k-inpainting-epoch-1.safetensors \
  --origin examples/input-inpainting.png --ootd examples/ootd.png \
  --prompt-file examples/prompt-inpainting.txt \
  --output output/inpainting.png --seed 123 --steps 40

python scripts/inference/inference.py --task editing \
  --model-dir models/Qwen-Image-Edit-2509 \
  --lora models/Garments2Look-LoRA/Qwen-Image-Edit-2509-LoRA-2-refer-20k-editing-epoch-1.safetensors \
  --origin examples/input-editing.png --ootd examples/ootd.png \
  --prompt-file examples/prompt-editing.txt \
  --output output/editing.png --seed 123 --steps 40
```

The script saves a PNG and a JSON run record with the prompt, parameters, and weight paths. It aligns the source image dimensions to multiples of 16, within the training pixel budget. `--task` labels the run; the input image and task-specific LoRA determine its behavior. Default guidance is 4.0.

### Validation

Validated on one H200: metadata generation for one training sample, one optimization step at a 65,536-pixel budget (finite loss and saved LoRA), and one 40-step inference per task at 960 × 1088. Full-scale and distributed training were not re-run. See [`validation.json`](./examples/validation.json) for the recorded checks.

### Output example

**Seed 123**

![Inpainting and editing example, seed 123](./examples/comparison.jpg)

Columns: **OOTD**, **inpainting input**, **inpainting output**, **editing input**, **editing output**. Full task prompts are printed as two separate lines below the images, spanning the entire figure width.

This white-studio test example contains six items: a light-blue shirt, patterned cardigan, gray trousers, brown loafers, a bag, and a belt. Styling annotations specify a partially unbuttoned and tucked-in shirt, an unbuttoned cardigan, and a belt around the waist; the layering order is shirt → belt → cardigan. The outfit was selected by the author from three candidates before inference. Sample provenance and parameters are recorded in [`manifest.json`](./examples/manifest.json), with individual images and prompt files alongside it. Both tasks use inference seed 123, second-epoch task-specific LoRAs, 40 steps, and guidance 4.0. This example is not an aggregate evaluation.

The default inference seed is **123**. Inputs, full prompts, outputs, and run records are provided in [`examples/`](./examples/).

After generating both task outputs into an example folder, render the five-column figure with:

```bash
python scripts/inference/compare_example.py --example-dir examples
```

To run your own outfit, replace `--origin`, `--ootd`, and `--prompt-file`. Figure 1 must be a masked person for inpainting or a source person for editing. Figure 2 must contain the target items in the same order as the numbered prompt. Include styling instructions and layering order in the prompt, and supply the LoRA trained for the selected task.

## Benchmark and release contents

See the paper for baseline comparisons, evaluation protocols, and metric definitions. Released model outputs are available in the [test-set comparison results](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look-Test-Set-Results).

| Resource | Location |
| --- | --- |
| Dataset annotations and image archives | [Hugging Face dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look) |
| Training and inference | [`scripts/`](./scripts/) |
| Test-set comparison outputs | [Results dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look-Test-Set-Results) |
| Paper, poster, and figures | Links above and [`docs/`](./docs/) |

This repository includes dataset preparation and LoRA training/inference for Qwen-Image-Edit-2509. Task-specific LoRA checkpoints are available on [Hugging Face](https://huggingface.co/ArtmeScienceLab/Garments2Look-LoRA). Editing-task inputs and improved v3 masks are available in the updated dataset.

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
