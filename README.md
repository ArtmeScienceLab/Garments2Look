# Garments2Look

> **Paper**: Garments2Look: A Multi-Reference Dataset for High-Fidelity Outfit-Level Virtual Try-On with Clothing and Accessories
>
> **Authors**: [Junyao Hu](https://junyaohu.github.io/), [Zhongwei Cheng](https://scholar.google.com/citations?user=ayN-dVwAAAAJ), [Waikeung Wong](https://research.polyu.edu.hk/en/persons/wai-keung-wong-2/), [Xingxing Zou](https://scholar.google.com/citations?user=UhnQA3UAAAAJ)

- [Project Page](https://junyaohu.github.io/garments2look-website/)
- [Dataset](https://huggingface.co/datasets/ArtmeScienceLab/Garments2Look)

# Abstract

Virtual try-on (VTON) has advanced single-garment visualization, yet real-world fashion centers on full outfits with multiple items, layering, fine-grained categories, and diverse styling—beyond current systems. Existing datasets are category-limited and lack outfit diversity. We introduce Garments2Look, the first large-scale multimodal dataset for outfit-level VTON, comprising 80K many-garments-to-one-look pairs across 40 major categories and 361+ fine-grained subcategories. Each pair includes 3-12 item images, a model image in a complete outfit, and detailed item and try-on annotations. We further design a synthesis pipeline balancing authenticity and diversity: it maximizes use of raw images for realism, and explicitly injects diverse styles and specific styling techniques during outfit/look synthesis. To probe task difficulty, we adapt SOTA VTON methods and general-purpose image editors to establish baselines. Results show current methods struggle to try on full outfits seamlessly and to infer correct layering, leading to misalignment and artifacts. All data will be open-sourced.

# Dataset
The dataset will be available at Hugging Face soon.

# Citation
```bibtex
@inproceedings{cvpr2026garments2look,
    title={Garments2Look: A Multi-Reference Dataset for High-Fidelity Outfit-Level Virtual Try-On with Clothing and Accessories},
    author={Hu, Junyao and Cheng, Zhongwei and Wong, Waikeung and Zou, Xingxing},
    booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
    year={2026}
}
```