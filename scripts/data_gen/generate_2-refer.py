#!/usr/bin/env python3
"""Generate 2-reference metadata for Qwen-Image-Edit LoRA training.

Each entry:
{
    "image": "<target look image>",
    "prompt": "<text prompt>",
    "edit_image": ["<reference look>", "<ootd collage>"]
}

Reference look:
- inpainting: agnostic look (person without garments)
- editing: edited look (partially edited look)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from torch.utils.data import ConcatDataset
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dataset import (
    MytheresaOutfitDataset,
    PolyvoreOutfitDataset,
    generate_agnostic_from_paths,
)

Task = Literal["inpainting", "editing"]
DEFAULT_DATASET_ROOT = Path(os.environ.get("G2L_DATASET_ROOT", "data/Garments2Look"))
DEFAULT_METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DEFAULT_AGNOSTIC_CACHE_DIR = PROJECT_ROOT / "data" / "agnostic_cache"


def gender_to_model(gender: str) -> str:
    return {
        "women": "woman",
        "men": "man",
        "boys": "boy",
        "girls": "girl",
    }.get(gender, "person")


_POLYVORE_TYPE_PHRASES = {
    "top": "t-shirt",
    "outwear": "jacket",
    "coat": "coat",
    "dress": "dress",
    "skirt": "skirt",
    "bottom": "pants",
    "pants": "pants",
    "jeans": "jeans",
    "shorts": "shorts",
    "shoes": "shoes",
    "boots": "boots",
    "bag": "bag",
    "backpack": "backpack",
    "earrings": "earrings",
    "necklace": "necklace",
    "bracelet": "bracelet",
    "brooch": "brooch",
    "belt": "belt",
    "hat": "hat",
    "glasses": "glasses",
    "sunglasses": "sunglasses",
    "scarf": "scarf",
    "gloves": "gloves",
    "watch": "watch",
    "ring": "ring",
}


def _phrase_from_jewelry_leaf(leaf: str) -> str:
    if "choker" in leaf:
        return "choker"
    if "earring" in leaf:
        return "earrings"
    if "necklace" in leaf or "pendant" in leaf:
        return "necklace"
    if "bracelet" in leaf:
        return "bracelet"
    if "cufflink" in leaf:
        return "cufflinks"
    if "ring" in leaf:
        return "ring"
    if "brooch" in leaf:
        return "brooch"
    return "jewelry"


def _phrase_from_mytheresa_type(garment_type: str) -> str:
    parts = [part.strip() for part in garment_type.split("::") if part.strip()]
    if not parts:
        return "garment"

    root = parts[0]
    mid = parts[1] if len(parts) > 1 else ""
    leaf = parts[-1].replace("-", " ")

    if root == "clothing":
        mid_map = {
            "tops": "top",
            "knitwear": "sweater",
            "jeans": "jeans",
            "pants": "pants",
            "shorts": "shorts",
            "skirts": "skirt",
            "dresses": "dress",
            "jumpsuits": "jumpsuit",
            "jackets": "jacket",
            "coats": "coat",
            "blazers": "blazer",
            "activewear": "activewear",
        }
        if mid in mid_map:
            return mid_map[mid]
        if "shirt" in leaf or "tee" in leaf or "top" in leaf:
            return "top"
        if "dress" in leaf:
            return "dress"
        if "skirt" in leaf:
            return "skirt"
        if "pant" in leaf or "trouser" in leaf:
            return "pants"
        if "short" in leaf:
            return "shorts"
        if "jacket" in leaf or "blazer" in leaf:
            return "jacket"
        if "coat" in leaf:
            return "coat"
        if "sweater" in leaf or "knit" in leaf:
            return "sweater"
        return leaf

    if root == "shoes":
        if "chelsea" in leaf:
            return "chelsea boots"
        if "ankle" in leaf or (mid == "boots" and "boot" in leaf):
            return "ankle boots"
        if "boot" in leaf or mid == "boots":
            return "boots"
        if mid == "flats" or "ballet flat" in leaf or "flat" in leaf:
            return "flats"
        if "loafer" in leaf:
            return "loafers"
        if "sneaker" in leaf:
            return "sneakers"
        if "sandal" in leaf:
            return "sandals"
        if "derby" in leaf or "oxford" in leaf:
            return "derby shoes"
        if "heel" in leaf or "pump" in leaf or "stiletto" in leaf:
            return "heels"
        if "slide" in leaf or "slipper" in leaf:
            return "slippers"
        if "espadrille" in leaf:
            return "espadrilles"
        return "shoes"

    if root in {"bags", "bag"}:
        return "bag"

    if root == "jewelry":
        return _phrase_from_jewelry_leaf(leaf)

    if root == "accessories":
        accessory_mid_map = {
            "ties": "tie",
            "socks": "socks",
            "belts": "belt",
            "scarves": "scarf",
            "hats": "hat",
            "gloves": "gloves",
            "eyewear": "sunglasses",
            "headwear": "hat",
            "wallets": "wallet",
            "watches": "watch",
            "headbands": "headband",
            "glasses": "glasses",
            "keychains": "keychain",
            "hair clips": "hair clip",
            "scrunchies": "scrunchie",
            "tights": "tights",
            "wings": "wings",
            "girls' bags": "bag",
            "silk pockets": "silk pocket",
            "washbags": "pouch",
            "girl's earmuffs": "earmuffs",
            "chains": "chain",
            "bag accessories": "bag charm",
            "phone cases": "phone case",
        }
        if mid in accessory_mid_map:
            return accessory_mid_map[mid]
        if mid == "jewelry" or "jewelry" in parts:
            return _phrase_from_jewelry_leaf(leaf)
        if "watch" in mid or "watch" in leaf:
            return "watch"
        if "wallet" in mid or "wallet" in leaf or "billfold" in leaf:
            return "wallet"
        if "goggle" in mid or "goggle" in leaf:
            return "goggles"
        if "earmuff" in mid or "earmuff" in leaf:
            return "earmuffs"
        if "wing" in mid or "wing" in leaf:
            return "wings"
        if "silk pocket" in mid or "pocket square" in leaf or "silk pocket" in leaf:
            return "silk pocket"
        if "washbag" in mid or "washbag" in leaf or "pouch" in leaf:
            return "pouch"
        if "phone case" in mid or "phone case" in leaf:
            return "phone case"
        if "bag accessory" in mid or "bag charm" in leaf or "charm" in leaf:
            return "bag charm"
        if "chain" in mid or "chain" in leaf:
            return "chain"
        if "bag" in mid:
            return "bag"
        if "belt" in leaf:
            return "belt"
        if "scarf" in leaf:
            return "scarf"
        if "tie" in leaf or "bow tie" in leaf:
            return "tie"
        if "sock" in leaf:
            return "socks"
        if "headband" in leaf:
            return "headband"
        if "keychain" in leaf:
            return "keychain"
        if "hat" in leaf:
            return "hat"
        if "glove" in leaf:
            return "gloves"
        if "sunglass" in leaf or "eyewear" in leaf or "glasses" in leaf:
            return "glasses"
        return "accessory"

    return leaf


def garment_type_to_phrase(garment_type: Optional[str]) -> str:
    if not garment_type:
        return "garment"
    normalized = garment_type.strip().lower()
    if "::" in normalized:
        return _phrase_from_mytheresa_type(normalized)
    return _POLYVORE_TYPE_PHRASES.get(normalized, normalized.replace("_", " "))


_GENERIC_INCLUDE_PHRASES = {
    "accessory",
    "garment",
    "jewelry",
    "shoes",
    "activewear",
}


def _infer_phrase_from_simple_name(simple_name: str) -> str:
    name = simple_name.lower()
    keyword_map = [
        (("bow tie", "bowtie"), "bow tie"),
        (("tie",), "tie"),
        (("choker",), "choker"),
        (("earring",), "earrings"),
        (("necklace", "pendant"), "necklace"),
        (("bracelet",), "bracelet"),
        (("cufflink",), "cufflinks"),
        (("brooch",), "brooch"),
        (("ring",), "ring"),
        (("wallet", "billfold"), "wallet"),
        (("watch",), "watch"),
        (("headband",), "headband"),
        (("keychain",), "keychain"),
        (("goggle",), "goggles"),
        (("scrunchie",), "scrunchie"),
        (("hair clip",), "hair clip"),
        (("pocket square", "silk pocket"), "silk pocket"),
        (("earmuff",), "earmuffs"),
        (("phone case",), "phone case"),
        (("bag charm", "charm"), "bag charm"),
        (("washbag", "pouch"), "pouch"),
        (("wing",), "wings"),
        (("chain",), "chain"),
        (("chelsea boot",), "chelsea boots"),
        (("ankle boot",), "ankle boots"),
        (("cowboy boot",), "boots"),
        (("boot",), "boots"),
        (("ballet flat", "ballet flats"), "flats"),
        (("flat",), "flats"),
        (("derby", "oxford"), "derby shoes"),
        (("loafer",), "loafers"),
        (("sneaker",), "sneakers"),
        (("sandal",), "sandals"),
        (("espadrille",), "espadrilles"),
        (("slipper", "slide"), "slippers"),
        (("pump", "stiletto", "heel"), "heels"),
        (("shoe",), "shoes"),
        (("sock",), "socks"),
        (("belt",), "belt"),
        (("scarf",), "scarf"),
        (("glove",), "gloves"),
        (("sunglass", "eyewear"), "sunglasses"),
        (("hat", "cap", "beanie"), "hat"),
        (("clutch", "backpack", "tote", "bag"), "bag"),
        (("blazer",), "blazer"),
        (("jacket", "bomber", "coat"), "jacket"),
        (("cardigan", "sweater", "knit"), "sweater"),
        (("dress",), "dress"),
        (("skirt",), "skirt"),
        (("jean",), "jeans"),
        (("trouser", "pant"), "pants"),
        (("short",), "shorts"),
        (("shirt", "blouse", "tee", "top"), "top"),
    ]
    for keywords, phrase in keyword_map:
        if any(keyword in name for keyword in keywords):
            return phrase
    return "garment"


def garment_to_include_phrase(
    garment_type: Optional[str], simple_name: str = ""
) -> str:
    phrase = garment_type_to_phrase(garment_type)
    if phrase not in _GENERIC_INCLUDE_PHRASES:
        return phrase
    inferred = _infer_phrase_from_simple_name(simple_name)
    return inferred if inferred != "garment" else phrase


_NO_ARTICLE_PHRASES = {
    "pants",
    "jeans",
    "shorts",
    "shoes",
    "boots",
    "sneakers",
    "loafers",
    "sandals",
    "heels",
    "earrings",
    "sunglasses",
    "glasses",
    "gloves",
    "socks",
    "slippers",
    "espadrilles",
}


def phrase_with_article(phrase: str) -> str:
    if phrase in _NO_ARTICLE_PHRASES:
        return phrase
    if phrase.startswith(("a ", "an ")):
        return phrase
    article = "an" if phrase[:1] in "aeiou" else "a"
    return f"{article} {phrase}"


def append_styling(text: str, styling: str) -> str:
    styling = (styling or "").strip()
    if styling:
        return f"{text} ({styling})"
    return text


def format_numbered_items(items: List[str]) -> str:
    return ", ".join(f"({index}) {item}" for index, item in enumerate(items, start=1))


def build_prompt(
    gender: str,
    outfit: List[str],
    outfit_all: Dict[str, str],
    outfit_info: Dict[str, Any],
    reference_look_path: str,
    ootd_image_path: str,
    garment_image_paths: Dict[str, str],
    garment_image_types: Optional[Dict[str, str]] = None,
) -> Tuple[str, List[str]]:
    garment_image_types = garment_image_types or {}
    dressing_details = outfit_info.get("dressing_details", {})
    styling_techniques = dressing_details.get("styling_techniques", {})
    layering_structure = dressing_details.get("layering_structure", [])

    model = gender_to_model(gender)
    numbered_entries: List[Tuple[str, str]] = []

    for garment_id in outfit:
        phrase = phrase_with_article(
            garment_to_include_phrase(
                garment_image_types.get(garment_id),
                outfit_all.get(garment_id, ""),
            )
        )
        numbered_entries.append(
            (garment_id, append_styling(phrase, styling_techniques.get(garment_id, "")))
        )

    for garment_id, simple_name in outfit_all.items():
        if garment_id in garment_image_paths or not simple_name:
            continue
        numbered_entries.append(
            (
                garment_id,
                append_styling(simple_name, styling_techniques.get(garment_id, "")),
            )
        )

    garment_index = {garment_id: index for index, (garment_id, _) in enumerate(numbered_entries, start=1)}
    include_count = len(outfit)

    text_prompt = (
        f"Keep the {model}'s identity, pose, background in Figure 1 unchanged, "
        f"wearing the outfit in Figure 2, include "
        f"{format_numbered_items([text for _, text in numbered_entries[:include_count]])}"
    )

    other_entries = numbered_entries[include_count:]
    if other_entries:
        and_parts = [
            f"({garment_index[garment_id]}) {text}"
            for garment_id, text in other_entries
        ]
        text_prompt += ". And " + ", ".join(and_parts) + "."
    else:
        text_prompt += "."

    if layering_structure:
        layering_refs = [
            f"({garment_index[garment_id]})"
            for garment_id in layering_structure
            if garment_id in garment_index
        ]
        if layering_refs:
            text_prompt += f" Layering Order: {' -> '.join(layering_refs)}."

    image_prompt = [reference_look_path, ootd_image_path]
    return text_prompt, image_prompt


def agnostic_cache_path(sample: Dict[str, Any], cache_dir: Path) -> Path:
    return cache_dir / sample.get("source", "unknown") / sample.get("gender", "unknown") / f"{sample.get('outfit_id', 'unknown')}.png"


def _is_valid_image(path: Path) -> bool:
    from PIL import Image

    try:
        with Image.open(path) as im:
            im.load()
        return True
    except Exception:
        return False


def save_agnostic_image(sample: Dict[str, Any], cache_dir: Path) -> Optional[str]:
    cache_path = agnostic_cache_path(sample, cache_dir)
    if cache_path.exists():
        if _is_valid_image(cache_path):
            return str(cache_path)
        try:
            cache_path.unlink()
        except OSError:
            pass

    agnostic_image = generate_agnostic_from_paths(
        sample.get("look_image_path"), sample.get("merged_mask_path")
    )
    if agnostic_image is None:
        return None

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Keep a real .png suffix so PIL can infer format even if interrupted mid-write.
    tmp_path = cache_path.parent / f"{cache_path.stem}.tmp.{os.getpid()}.png"
    agnostic_image.save(tmp_path, format="PNG")
    os.replace(tmp_path, cache_path)
    return str(cache_path)


def get_reference_look_path(
    sample: Dict[str, Any], task: Task, agnostic_cache_dir: Path
) -> Optional[str]:
    if task == "inpainting":
        return save_agnostic_image(sample, agnostic_cache_dir)
    return sample.get("edited_look_image_path")


def save_ootd(sample: Dict[str, Any], cache_dir: Path) -> Optional[str]:
    """Use the supplied collage or build a row-major grid in prompt item order."""
    from PIL import Image, ImageOps
    existing = sample.get("ootd_image_path")
    if existing and Path(existing).is_file():
        return existing
    paths = [sample["garment_image_paths"].get(item) for item in sample.get("outfit", [])]
    if not paths or not all(path and Path(path).is_file() for path in paths):
        return None
    import math
    columns = min(3, len(paths))
    rows = math.ceil(len(paths) / columns)
    cell = 384
    canvas = Image.new("RGB", (columns * cell, rows * cell), "white")
    for idx, path in enumerate(paths):
        with Image.open(path) as image:
            tile = ImageOps.contain(image.convert("RGB"), (cell, cell))
        canvas.paste(tile, ((idx % columns)*cell+(cell-tile.width)//2, (idx // columns)*cell+(cell-tile.height)//2))
    output = cache_dir / sample.get("source", "unknown") / sample.get("gender", "unknown") / (str(sample["outfit_id"])+".png")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    return str(output)


def sample_to_entry(
    sample: Dict[str, Any], task: Task, agnostic_cache_dir: Path
) -> Optional[Dict[str, Any]]:
    outfit = sample.get("outfit", [])
    if not outfit:
        return None

    reference_look_path = get_reference_look_path(sample, task, agnostic_cache_dir)
    look_image_path = sample.get("look_image_path")
    ootd_image_path = save_ootd(sample, agnostic_cache_dir.parent / "ootd_cache")
    if not reference_look_path or not look_image_path or not ootd_image_path or not all(Path(p).is_file() for p in [reference_look_path, look_image_path, ootd_image_path]):
        return None

    text_prompt, image_prompt = build_prompt(
        gender=sample.get("gender", ""),
        outfit=outfit,
        outfit_all=sample.get("outfit_all", {}),
        outfit_info=sample.get("outfit_info", {}),
        garment_image_paths=sample.get("garment_image_paths", {}),
        garment_image_types=sample.get("garment_image_types", {}),
        reference_look_path=reference_look_path,
        ootd_image_path=ootd_image_path,
    )

    return {
        "image": look_image_path,
        "prompt": text_prompt,
        "edit_image": image_prompt,
    }


def default_output_path(
    task: Task,
    section: str,
    num_samples: Optional[int],
    timestamp: Optional[str] = None,
) -> Path:
    ts_suffix = f"-{timestamp}" if timestamp else ""
    if num_samples is None:
        filename = f"garments2look-2-refer-{task}-{section}{ts_suffix}.json"
    else:
        filename = f"garments2look-2-refer-{task}-{section}-{num_samples}{ts_suffix}.json"
    return DEFAULT_METADATA_DIR / filename


def load_dataset(dataset_root: Path, section: str) -> ConcatDataset:
    mytheresa = MytheresaOutfitDataset(dataset_root=dataset_root, section=section)
    polyvore = PolyvoreOutfitDataset(dataset_root=dataset_root, section=section)
    return ConcatDataset([mytheresa, polyvore])


def select_indices(total_count: int, num_samples: Optional[int], seed: int) -> List[int]:
    if num_samples is None or num_samples >= total_count:
        return list(range(total_count))
    rng = random.Random(seed)
    return rng.sample(range(total_count), num_samples)


_WORKER_STATE: Dict[str, Any] = {}


def _init_worker(
    dataset_root: str, section: str, task: str, agnostic_cache_dir: str
) -> None:
    _WORKER_STATE["dataset"] = load_dataset(Path(dataset_root), section)
    _WORKER_STATE["task"] = task
    _WORKER_STATE["cache"] = Path(agnostic_cache_dir)


def _process_index(idx: int) -> Optional[Dict[str, Any]]:
    return sample_to_entry(
        _WORKER_STATE["dataset"][idx],
        _WORKER_STATE["task"],
        _WORKER_STATE["cache"],
    )


def build_metadata(
    indices: List[int],
    dataset: ConcatDataset,
    task: Task,
    agnostic_cache_dir: Path,
    dataset_root: Path,
    section: str,
    num_workers: int,
) -> Tuple[List[Dict[str, Any]], int]:
    if num_workers <= 1:
        metadata_list: List[Dict[str, Any]] = []
        skip_count = 0
        for idx in tqdm(indices, desc=f"{task}-{section}"):
            entry = sample_to_entry(dataset[idx], task, agnostic_cache_dir)
            if entry is None:
                skip_count += 1
                continue
            metadata_list.append(entry)
        return metadata_list, skip_count

    metadata_list = []
    skip_count = 0
    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=_init_worker,
        initargs=(str(dataset_root), section, task, str(agnostic_cache_dir)),
    ) as executor:
        for entry in tqdm(
            executor.map(_process_index, indices, chunksize=16),
            total=len(indices),
            desc=f"{task}-{section} x{num_workers}",
        ):
            if entry is None:
                skip_count += 1
                continue
            metadata_list.append(entry)
    return metadata_list, skip_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 2-reference metadata for inpainting or editing."
    )
    parser.add_argument(
        "--task",
        required=True,
        choices=["inpainting", "editing"],
        help="inpainting: agnostic look + ootd; editing: edited look + ootd",
    )
    parser.add_argument(
        "--section",
        default="train",
        choices=["train", "test"],
        help="Dataset split to use",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=8,
        help="Number of outfits to sample (use 0 for all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=123,
        help="Random seed for sampling",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=32,
        help="Parallel workers for metadata generation",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
        help="Garments2Look dataset root",
    )
    parser.add_argument(
        "--agnostic-cache-dir",
        type=Path,
        default=DEFAULT_AGNOSTIC_CACHE_DIR,
        help="Directory to cache generated agnostic images for metadata export",
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="Optional suffix for output filename, e.g. 250902-0908",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/metadata/garments2look-2-refer-<task>-<section>[-<n>][-<timestamp>].json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task: Task = args.task
    num_samples = None if args.num_samples == 0 else args.num_samples
    output_path = args.output or default_output_path(
        task, args.section, num_samples, args.timestamp
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Task: {task}")
    print(f"Section: {args.section}")
    print(f"Dataset root: {args.dataset_root}")
    print(f"Num workers: {args.num_workers}")
    print("Loading datasets...")
    dataset = load_dataset(args.dataset_root, args.section)
    total_count = len(dataset)
    print(f"Total outfits: {total_count}")

    indices = select_indices(total_count, num_samples, args.seed)
    print(f"Processing {len(indices)} outfits...")

    metadata_list, skip_count = build_metadata(
        indices=indices,
        dataset=dataset,
        task=task,
        agnostic_cache_dir=args.agnostic_cache_dir,
        dataset_root=args.dataset_root,
        section=args.section,
        num_workers=args.num_workers,
    )

    if not metadata_list:
        raise RuntimeError("No usable samples. Check look/reference images and masks (inpainting) or edited inputs (editing).")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)

    print("Done.")
    print(f"  Written: {len(metadata_list)}")
    print(f"  Skipped: {skip_count}")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()
