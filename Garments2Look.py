import json
import os
from typing import List, Dict, Any, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import random
from torch.utils.data import Dataset, ConcatDataset

# for unknown ID garment, infer its category by its simple name
garment_category_order = {
    "clothing::top/full": {
        "tops", "top", "shirts", "jackets", "blazers", "bras", "bralette", "coats",
        "knitwear", "hoodies", "sweaters", "outwear", "cover-ups", "tailoring",
        "base layers upper", "dresses", "dress", "jumpsuits", "jumpsuit", "swimsuits",
        "bikinis sets", "bikinis", "bodysuits", "playsuits", "outfits", "skiwear",
        "swimwear", "underwear", "nightwear", "bathtime",
    },
    "clothing::bottom": {
        "jeans", "pants", "shorts", "skirts", "skirt", "briefs", "boxers",
        "bikinis bottoms", "base layers lower",
    },
    "shoes": {
        "shoes", "boots", "loafers", "sandals", "sneakers", "espadrilles", "flats",
        "heels", "mules", "pumps",
    },
    "bag": {
        "bags", "bag", "wallet", "backpack", "briefcase", 
        "card holder", "clutch", "pouch",
    },
    "accessory::hair": {
        "hair clips", "scrunchies", "hairwear",
        "hair clip", "scrunchie"
    },
    "accessory::head": {
        "hats", "helmets", "headbands", "masks",
        "hat", "helmet", "headband", "mask",
    },
    "accessory::eye": {
        "eyewear", "sunglasses", "glasses", "goggles",
    },
    "accessory::ear": {
        "earrings", "earmuffs",
        "earring", "earmuff",
    },
    "accessory::neck": {
        "necklaces", "necklace", "bowtie", "bow tie", "tie", "scarves", "scarf", "choker", 
        "cufflink", "tie clip", "neckwear", "bib", "collar",
    },
    "accessory::chest": {
        "brooches", "brooch", "badge", "silk pocket",
    },
    "accessory::wrist": {
        "watches", "bracelets", "bracelet"
    },
    "accessory::hand": {
        "gloves",
    },
    "accessory::finger": {
        "ring",
    },
    "accessory::waist": {
        "belt", 
    },
    "accessory::leg": {
        "legging", "tight", "sock", "legwear", "anklet",
    },
    "accessory::bag": {
        "bag accessory", "bag charm", "keychain",
    },
    "accessory::other": {
        "ball", "wing", "chain", "phone case", "unknown",
    }
}

# for unknown ID garment, infer its category by its simple name
def infer_category_by_simple_name(simple_name: str) -> str:
    simple_name = simple_name.lower()
    name_words = (
        simple_name.replace("::", " ")
        .replace("/", " ")
        .replace("-", " ")
        .split()
    )

    best_cat = "other"
    best_score = 0

    for main_cat, keywords in garment_category_order.items():
        score = 0
        for kw in keywords:
            if not kw:
                continue

            # 中等优先级：在词级别上精确匹配
            if kw in name_words:
                score = max(score, 2)

            # 兜底：任意子串匹配
            if kw in simple_name:
                score = max(score, 1)

        # 按得分选择最优类别
        if score > best_score:
            best_score = score
            best_cat = main_cat

    return best_cat if best_score > 0 else "other"


class MytheresaOutfitDataset(Dataset):
    """
    Mytheresa Garments2Look Dataset
    """

    def __init__(
        self,
        dataset_root: str,
        section: Optional[str] = None,
    ):
        """
        Args:
            dataset_root: Root directory of the dataset
            section: Dataset split to use, can be "train" or "test", None means no filtering
        """
        self.dataset_root = dataset_root
        self.section = section
        
        # Build all paths based on root directory
        self.image_json = os.path.join(dataset_root, "mytheresa_image_v1.0_2512.json")
        # self.outfit_json = os.path.join(dataset_root, "mytheresa_outfit_v1.1_2512.json")
        self.outfit_json = os.path.join(dataset_root, "mytheresa_outfit_v1.0_2512.json")
        self.garment_root = os.path.join(dataset_root, "mytheresa", "images")
        self.look_root = os.path.join(dataset_root, "mytheresa", "looks-resized")
        self.mask_root = os.path.join(dataset_root, "mytheresa", "annotations", "mask-sam3-resized")

        # Load JSON files
        with open(self.image_json, "r", encoding="utf-8") as f:
            self.image_data: Dict[str, Any] = json.load(f)
        with open(self.outfit_json, "r", encoding="utf-8") as f:
            self.outfit_data: Dict[str, Any] = json.load(f)

        # Pre-build list of available samples
        self.samples = []
        for outfit_id, current_outfit in self.outfit_data.items():
            if self.section is not None:
                outfit_section = current_outfit.get("section")
                if outfit_section != self.section:
                    continue
            self.samples.append(outfit_id)

        # section_info = f" (section={self.section})" if self.section is not None else ""
        # print(f"MytheresaOutfitDataset: Found {len(self.samples)} valid samples{section_info}")

    

    # -------------------- Internal utility functions --------------------
    def _get_garment_images(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Returns a dictionary of garment image paths.
        """
        images: Dict[str, Optional[str]] = {} # key: garment_id, value: image_path
        garment_ids = current_outfit.get("outfit", [])

        for garment_id in garment_ids:
            if garment_id.startswith("U"):
                continue
            garment_info = self.image_data.get(garment_id)
            if garment_info is None:
                print(f"Garment {garment_id} not found in image data")
                continue

            images_dict = garment_info.get("images", {})
            product_dict = images_dict.get("product", {})
            garment_full_images = product_dict.get("full", [])
            if not garment_full_images:
                print(f"Garment {garment_id} has no full images")
                continue

            image_path = os.path.join(
                self.garment_root, garment_id, garment_full_images[0]
            )
            if os.path.exists(image_path):
                images[garment_id] = image_path
            else:
                print(f"Garment {garment_id} has no full images")

        return images # key: garment_id, value: image_path

    def _get_garment_images_types(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Returns a dictionary of garment types.
        """
        types: Dict[str, Optional[str]] = {} # key: garment_id, value: garment_type
        main_categories: Dict[str, Optional[str]] = {} # key: garment_id, value: main_category

        garment_ids = current_outfit.get("outfit", [])

        for garment_id in garment_ids:
            garment_info = self.image_data.get(garment_id)
            if garment_info is None:
                continue

            images_dict = garment_info.get("images", {})
            product_dict = images_dict.get("product", {})
            garment_full_images = product_dict.get("full", [])
            if not garment_full_images:
                continue

            image_path = os.path.join(
                self.garment_root, garment_id, garment_full_images[0]
            )
            if os.path.exists(image_path):
                types[garment_id] = garment_info.get("type", "")
                main_categories[garment_id] = garment_info.get("main_category", "")

        return types, main_categories

    def _get_look_image(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        """
        Get look image path.
        Path format: {look_root}/{gender}/{outfit_id}.png or {outfit_id}.jpg
        Automatically detects whether the file is png or jpg format
        """
        gender = current_outfit.get("gender", "unknown")
        # Try png first
        image_png = os.path.join(self.look_root, gender, f"{outfit_id}.png")
        if os.path.exists(image_png):
            return image_png
        # Then try jpg
        image_jpg = os.path.join(self.look_root, gender, f"{outfit_id}.jpg")
        if os.path.exists(image_jpg):
            return image_jpg
        print(f"MytheresaOutfitDataset: Look image not found: {image_png} or {image_jpg}")
        return None

    def _get_garments_mask(self, current_outfit: Dict[str, Any], outfit_id: str) -> Tuple[Optional[str], Dict[str, List[str]]]:
        """
        Get the merged mask image path and all segmented results for the corresponding outfit id.
        
        Args:
            current_outfit: Dictionary information of the current outfit
            outfit_id: Outfit ID
            
        Returns:
            tuple[Optional[str], Dict[str, List[str]]]: 
                - First return value: merged_mask_path (str), merged mask path, returns None if not exists
                - Second return value: mask_paths (dict), keys are garment IDs, values are string lists storing all mask paths for the corresponding garment
        """
        gender = current_outfit.get("gender", "unknown")
        outfit_mask_dir = os.path.join(
            self.mask_root,
            gender,
            str(outfit_id),
        )
        
        # Get merged mask path
        merged_mask_path = os.path.join(outfit_mask_dir, "merged_mask.png")
        if not os.path.exists(merged_mask_path):
            print(f"MytheresaOutfitDataset: Merged mask not found: {merged_mask_path}")
            merged_mask_path = None
        
        # Get all segmented mask paths
        mask_paths: Dict[str, List[str]] = {}
        
        # If directory does not exist, return empty dict
        if not os.path.exists(outfit_mask_dir):
            return merged_mask_path, mask_paths
        
        # Scan directory to find all mask files for each garment
        if os.path.exists(outfit_mask_dir):
            for filename in os.listdir(outfit_mask_dir):
                # Skip merged_mask.png and color_segmentation.png
                if filename in ["merged_mask.png", "color_segmentation.png"]:
                    continue
                
                # Filename format: {garment_id}-{index}.png
                if filename.endswith(".png"):
                    full_path = os.path.join(outfit_mask_dir, filename)
                    # Extract garment_id (remove suffix and index)
                    base_name = filename[:-4]  # Remove .png
                    garment_id = base_name.split("-")[0]
                    if garment_id not in mask_paths:
                        mask_paths[garment_id] = []
                    mask_paths[garment_id].append(full_path)
        
        return merged_mask_path, mask_paths

    # -------------------- Dataset interface --------------------
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        outfit_id = self.samples[idx]
        current_outfit = self.outfit_data[outfit_id]

        garment_image_paths = self._get_garment_images(current_outfit)
        garment_image_types, main_categories = self._get_garment_images_types(current_outfit)
        look_image_path = self._get_look_image(current_outfit, outfit_id)
        _, garments_mask_paths = self._get_garments_mask(current_outfit, outfit_id)
        outfit_list = list(current_outfit.get("outfit").keys())
        outfit_info = current_outfit.get("outfit_info", {})
        
        # Build metadata
        metadata = {
            "id": outfit_id,
            "is_official_look": current_outfit.get("is_official_look"),
            "is_official_outfit": current_outfit.get("is_official_outfit"),
            "section": current_outfit.get("section"),
            "source": "mytheresa",
        }
        
        # Build outfit_info
        outfit_info_new = {
            "gender": current_outfit.get("gender", "N/A"),
            "look_image_path": look_image_path,
            "outfit_list": outfit_list,
        }
        
        # Build item_info
        item_info = {}
        layering_structure = outfit_info.get("dressing_details", {}).get("layering_structure", [])
        styling_techniques = outfit_info.get("dressing_details", {}).get("styling_techniques", {})
        
        # Build item_info for each garment
        for garment_id in outfit_list:
            simple_name = current_outfit.get("outfit").get(garment_id)
            main_category = main_categories.get(garment_id, None)
            if main_category is None:
                main_category = infer_category_by_simple_name(simple_name)
            item_data = {
                "simple_name": simple_name,
                "layering_structure": layering_structure.index(garment_id) if garment_id in layering_structure else -1,
                "styling_technique": styling_techniques.get(garment_id, None),
                "garment_image_type": garment_image_types.get(garment_id, None),
                "main_category": main_category,
                "garment_image_path": garment_image_paths.get(garment_id, None),
                "garment_mask_path": garments_mask_paths.get(garment_id)[0] if garments_mask_paths.get(garment_id, []) else None,
            }
            item_info[garment_id] = item_data
        
        return {
            "metadata": metadata,
            "outfit_info": outfit_info_new,
            "item_info": item_info,
        }


class PolyvoreOutfitDataset(Dataset):
    """
    Polyvore Garments2Look Dataset
    """

    def __init__(
        self,
        dataset_root: str,
        section: Optional[str] = None,
    ):
        """
        Args:
            dataset_root: Root directory of the dataset, e.g., "/mnt/data/hjy/datasets/Garments2Look"
            section: Dataset split to use, can be "train" or "test", None means no filtering
        """
        self.dataset_root = dataset_root
        self.section = section
        
        # Build all paths based on root directory
        self.image_json = os.path.join(dataset_root, "polyvore_image_v1.0_2512.json")
        # self.outfit_json = os.path.join(dataset_root, "polyvore_outfit_v1.1_2512.json")
        self.outfit_json = os.path.join(dataset_root, "polyvore_outfit_v1.0_2512.json")
        self.garment_root = os.path.join(dataset_root, "polyvore", "images")
        self.look_root = os.path.join(dataset_root, "polyvore", "looks-resized")
        self.mask_root = os.path.join(dataset_root, "polyvore", "annotations", "mask-sam3-resized")

        with open(self.image_json, "r", encoding="utf-8") as f:
            self.image_data: Dict[str, Any] = json.load(f)
        with open(self.outfit_json, "r", encoding="utf-8") as f:
            self.outfit_data: Dict[str, Any] = json.load(f)

        self.samples: List[str] = []
        for outfit_id, current_outfit in self.outfit_data.items():
            if self.section is not None:
                outfit_section = current_outfit.get("section")
                if outfit_section != self.section:
                    continue
            self.samples.append(outfit_id)

        # section_info = f" (section={self.section})" if self.section is not None else ""
        # print(f"PolyvoreOutfitDataset: Found {len(self.samples)} valid samples{section_info}")


    # -------------------- Internal utility functions --------------------
    def _get_garment_images(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        images: Dict[str, Optional[str]] = {} # key: garment_id, value: image_path
        garment_ids = current_outfit.get("outfit", [])
        gender = current_outfit.get("gender", "unknown")

        for garment_id in garment_ids:
            if garment_id.startswith("U"):
                continue
            garment_info = self.image_data.get(garment_id)
            if garment_info is None:
                print(f"PolyvoreOutfitDataset: Garment {garment_id} not found in image data")
                continue

            # type is now just "bag" format, no longer contains "women::" prefix
            garment_type = garment_info.get("type", "")
            # Build path: {garment_root}/{gender}/{type}/{garment_id}.jpg
            image_path = os.path.join(
                self.garment_root,
                gender,
                garment_type,
                f"{garment_id}.jpg",
            )
            if os.path.exists(image_path):
                images[garment_id] = image_path

        return images # key: garment_id, value: image_path

    def _get_garment_images_types(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Returns a dictionary of garment types.
        """
        types: Dict[str, Optional[str]] = {} # key: garment_id, value: garment_type
        main_categories: Dict[str, Optional[str]] = {} # key: garment_id, value: main_category
        garment_ids = current_outfit.get("outfit", [])
        gender = current_outfit.get("gender", "unknown")

        for garment_id in garment_ids:
            garment_info = self.image_data.get(garment_id)
            if garment_info is None:
                continue

            # type is now just "bag" format, no longer contains "women::" prefix
            garment_type = garment_info.get("type", "")
            # Build path: {garment_root}/{gender}/{type}/{garment_id}.jpg
            image_path = os.path.join(
                self.garment_root,
                gender,
                garment_type,
                f"{garment_id}.jpg",
            )
            if os.path.exists(image_path):
                # Get garment type information
                types[garment_id] = garment_type
                main_categories[garment_id] = garment_info.get("main_category")

        return types, main_categories

    def _get_look_image(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        gender = current_outfit.get("gender", "unknown")
        # Try png first
        image_png = os.path.join(self.look_root, gender, f"{outfit_id}.png")
        if os.path.exists(image_png):
            return image_png
        # Then try jpg
        image_jpg = os.path.join(self.look_root, gender, f"{outfit_id}.jpg")
        if os.path.exists(image_jpg):
            return image_jpg
        print(f"PolyvoreOutfitDataset: Look image not found: {image_png} or {image_jpg}")
        return None
    
    def _get_garments_mask(self, current_outfit: Dict[str, Any], outfit_id: str) -> Tuple[Optional[str], Dict[str, List[str]]]:
        """
        Get the merged mask image path and all segmented results for the corresponding outfit id.
        
        Args:
            current_outfit: Dictionary information of the current outfit
            outfit_id: Outfit ID
            
        Returns:
            tuple[Optional[str], Dict[str, List[str]]]: 
                - First return value: merged_mask_path (str), merged mask path, returns None if not exists
                - Second return value: mask_paths (dict), keys are garment IDs, values are string lists storing all mask paths for the corresponding garment
        """
        gender = current_outfit.get("gender", "unknown")
        outfit_mask_dir = os.path.join(
            self.mask_root,
            gender,
            str(outfit_id),
        )
        
        # Get merged mask path
        merged_mask_path = os.path.join(outfit_mask_dir, "merged_mask.png")
        if not os.path.exists(merged_mask_path):
            print(f"MytheresaOutfitDataset: Merged mask not found: {merged_mask_path}")
            merged_mask_path = None
        
        # Get all segmented mask paths
        mask_paths: Dict[str, List[str]] = {}
        
        # If directory does not exist, return empty dict
        if not os.path.exists(outfit_mask_dir):
            return merged_mask_path, mask_paths
        
        # Scan directory to find all mask files for each garment
        if os.path.exists(outfit_mask_dir):
            for filename in os.listdir(outfit_mask_dir):
                # Skip merged_mask.png and color_segmentation.png
                if filename in ["merged_mask.png", "color_segmentation.png"]:
                    continue
                
                # Filename format: {garment_id}-{index}.png
                if filename.endswith(".png"):
                    full_path = os.path.join(outfit_mask_dir, filename)
                    # Extract garment_id (remove suffix and index)
                    base_name = filename[:-4]  # Remove .png
                    garment_id = base_name.split("-")[0]
                    if garment_id not in mask_paths:
                        mask_paths[garment_id] = []
                    mask_paths[garment_id].append(full_path)
        
        return merged_mask_path, mask_paths

    # -------------------- Dataset interface --------------------
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        outfit_id = self.samples[idx]
        current_outfit = self.outfit_data[outfit_id]

        garment_image_paths = self._get_garment_images(current_outfit)
        garment_image_types, main_categories = self._get_garment_images_types(current_outfit)
        look_image_path = self._get_look_image(current_outfit, outfit_id)
        _, garments_mask_paths = self._get_garments_mask(current_outfit, outfit_id)
        outfit_list = list(current_outfit.get("outfit").keys())
        outfit_info = current_outfit.get("outfit_info", {})
        
        # Build metadata
        metadata = {
            "id": outfit_id,
            "is_official_look": current_outfit.get("is_official_look"),
            "is_official_outfit": current_outfit.get("is_official_outfit"),
            "section": current_outfit.get("section"),
            "source": "polyvore",
        }
        
        # Build outfit_info
        outfit_info_new = {
            "gender": current_outfit.get("gender", "N/A"),
            "look_image_path": look_image_path,
            "outfit_list": outfit_list,
        }
        
        # Build item_info
        item_info = {}
        layering_structure = outfit_info.get("dressing_details", {}).get("layering_structure", [])
        styling_techniques = outfit_info.get("dressing_details", {}).get("styling_techniques", {})
        
        # Build item_info for each garment
        for garment_id in outfit_list:
            simple_name = current_outfit.get("outfit").get(garment_id)
            main_category = main_categories.get(garment_id, None)
            if main_category is None:
                main_category = infer_category_by_simple_name(simple_name)
            item_data = {
                "simple_name": simple_name,
                "layering_structure": layering_structure.index(garment_id) if garment_id in layering_structure else -1,
                "styling_technique": styling_techniques.get(garment_id, None),
                "garment_image_type": garment_image_types.get(garment_id, None),
                "main_category": main_category,
                "garment_image_path": garment_image_paths.get(garment_id, None),
                "garment_mask_path": garments_mask_paths.get(garment_id)[0] if garments_mask_paths.get(garment_id, []) else None,
            }
            item_info[garment_id] = item_data
        
        return {
            "metadata": metadata,
            "outfit_info": outfit_info_new,
            "item_info": item_info,
        }


class Garments2LookDataset(Dataset):
    """
    Garments2Look Dataset that combines Mytheresa and Polyvore datasets.
    This class internally uses ConcatDataset to merge the two datasets.
    """

    def __init__(
        self,
        dataset_root: str,
        section: Optional[str] = None,
    ):
        """
        Args:
            dataset_root: Root directory of the dataset
            section: Dataset split to use, can be "train" or "test", None means no filtering
        """
        self.dataset_root = dataset_root
        self.section = section
        self.garment_category_order = garment_category_order
        
        # Create Mytheresa and Polyvore datasets
        mytheresa_dataset = MytheresaOutfitDataset(
            dataset_root=dataset_root,
            section=section,
        )
        # mytheresa_dataset = torch.utils.data.dataset.Subset(mytheresa_dataset, indices=range(10))
        polyvore_dataset = PolyvoreOutfitDataset(
            dataset_root=dataset_root,
            section=section,
        )
        # polyvore_dataset = torch.utils.data.dataset.Subset(polyvore_dataset, indices=range(10))
        
        # Combine datasets using ConcatDataset
        self.concat_dataset = ConcatDataset([mytheresa_dataset, polyvore_dataset])
        
        section_info = f" (section={section})" if section is not None else ""
        print(f"Garments2LookDataset: Combined dataset with {len(self.concat_dataset)} samples{section_info}")

    def __len__(self) -> int:
        return len(self.concat_dataset)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        data = self.concat_dataset[idx]
        
        # Load images
        data["outfit_info"]["look_image_pil"] = Image.open(data["outfit_info"]["look_image_path"])
        
        for _, garment_data in data["item_info"].items():

            if garment_data["garment_image_path"]:
                garment_data["garment_image_pil"] = Image.open(garment_data["garment_image_path"])
            else:
                garment_data["garment_image_pil"] = None

        return data

    @staticmethod
    def collate_fn(batch):
        outfit_id                   = [data['metadata']['id'] for data in batch]
        gender                      = [data['outfit_info']['gender'] for data in batch]
        input_order                 = [data['outfit_info']['input_list'] for data in batch]
        look_image_path             = [data['outfit_info']['look_image_path'] for data in batch]
        look_image_pils             = [data['outfit_info']['look_image_pil'] for data in batch]
        item_info                   = [data['item_info'] for data in batch]

        return {
            "outfit_id": outfit_id,
            "gender": gender,
            "input_list": input_list,
            "look_image_pils": look_image_pils,
            "look_image_path": look_image_path,
            "item_info": item_info,
        }


def _json_default(obj: Any):
    """
    Helper function to make dataset items JSON 可序列化.
    目前主要处理 PIL.Image 对象，导出其基础信息。
    """
    if isinstance(obj, Image.Image):
        return tuple(obj.size),
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


if __name__ == "__main__":
    from tqdm import tqdm
    import torch

    ROOT_DIR = "/mount/process/hjy/datasets/Garments2Look"

    #########################################################
    # Mytheresa dataset

    # def mytheresa_collate_fn(batch):
    #     return {
    #         "metadata": [data['metadata'] for data in batch],
    #         "item_info": [data['item_info'] for data in batch],
    #         "outfit_info": [data['outfit_info'] for data in batch],
    #     }

    # mytheresa_dataset = MytheresaOutfitDataset(dataset_root=ROOT_DIR)

    # for i in tqdm(range(len(mytheresa_dataset)), desc="Processing mytheresa dataset"):
    #     _ = mytheresa_dataset[i]

    # mytheresa_dataset_loader = torch.utils.data.DataLoader(mytheresa_dataset, batch_size=1, shuffle=False, collate_fn=mytheresa_collate_fn)
    # for data in tqdm(mytheresa_dataset_loader, desc="Processing mytheresa dataset"):
    #     _ = data

    #########################################################
    # Polyvore dataset

    # def polyvore_collate_fn(batch):
    #     return {
    #         "metadata": [data['metadata'] for data in batch],
    #         "item_info": [data['item_info'] for data in batch],
    #         "outfit_info": [data['outfit_info'] for data in batch],
    #     }

    # polyvore_dataset = PolyvoreOutfitDataset(dataset_root=ROOT_DIR)

    # for i in tqdm(range(len(polyvore_dataset)), desc="Processing polyvore dataset"):
    #     _ = polyvore_dataset[i]
    
    # polyvore_dataset_loader = torch.utils.data.DataLoader(polyvore_dataset, batch_size=1, shuffle=False, collate_fn=polyvore_collate_fn)
    # for data in tqdm(polyvore_dataset_loader, desc="Processing polyvore dataset"):
    #     _ = data

    #########################################################
    # Garments2Look dataset

    dataset = Garments2LookDataset(dataset_root=ROOT_DIR)

    for i in tqdm(range(len(dataset)), desc="Processing garments2look dataset"):
        data = dataset[i]
        print(json.dumps(data, ensure_ascii=False, indent=4, default=_json_default))
        break

    # import time
    # dataset_loader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)
    # for data in tqdm(dataset_loader, desc="Processing dataset"):
    #     _ = data
    #     time.sleep(1)
        # print(json.dumps(data, ensure_ascii=False, indent=4, default=_json_default))