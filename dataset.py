import json
import os
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image
from torch.utils.data import Dataset



def generate_agnostic_from_paths(
    look_image_path: Optional[str], look_mask_path: Optional[str]
) -> Optional[Image.Image]:
    """Generate agnostic look from mask-v3 (same logic as Garments2Look-TPAMI)."""
    if not look_image_path or not look_mask_path:
        return None
    if not os.path.exists(look_image_path) or not os.path.exists(look_mask_path):
        return None
    look_rgb = Image.open(look_image_path).convert("RGB")
    mask = Image.open(look_mask_path).convert("L")
    if mask.size != look_rgb.size:
        mask = mask.resize(look_rgb.size, Image.NEAREST)
    mask_np = np.array(mask)
    look_np = np.array(look_rgb)
    garment_region = mask_np > 127
    out = look_np.copy()
    out[garment_region] = (128, 128, 128)
    return Image.fromarray(out)


def get_merged_mask_v3_path(
    mask_v3_root: str, gender: str, outfit_id: str
) -> Optional[str]:
    path = os.path.join(mask_v3_root, gender, f"{outfit_id}.png")
    return path if os.path.exists(path) else None


def parse_outfit_fields(current_outfit: Dict[str, Any]) -> Tuple[List[str], Dict[str, str]]:
    """Parse outfit ids and id->name mapping from outfit JSON."""
    raw_outfit = current_outfit.get("outfit")
    if isinstance(raw_outfit, dict):
        outfit_all = dict(raw_outfit)
        return list(raw_outfit.keys()), outfit_all

    outfit_ids = list(raw_outfit or [])
    outfit_all = {
        list(item.keys())[0]: list(item.values())[0]
        for item in (current_outfit.get("outfit_all") or [])
    }
    return outfit_ids, outfit_all


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
        self.source = "mytheresa"
        self.section = section

        # Build all paths based on root directory
        self.image_json = os.path.join(dataset_root, "mytheresa_image_v1.0_2512.json")
        self.outfit_json = os.path.join(dataset_root, "mytheresa_outfit_v1.1_2512.json")
        if not os.path.isfile(self.outfit_json):
            self.outfit_json = os.path.join(dataset_root, "mytheresa_outfit_v1.0_2512.json")
        self.garment_root = os.path.join(dataset_root, "mytheresa", "images")
        self.look_root = os.path.join(dataset_root, "mytheresa", "looks-resized")
        self.look_edited_root = os.path.join(dataset_root, "mytheresa", "edited", "banana")
        self.mask_v3_root = os.path.join(
            dataset_root, "mytheresa", "annotations", "mask-v3-look-resized"
        )
        self.ootd_root = os.path.join(dataset_root, "mytheresa", "ootd")

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

        section_info = f" (section={self.section})" if self.section is not None else ""
        print(f"MytheresaOutfitDataset: Found {len(self.samples)} valid samples{section_info}")

    # -------------------- Internal utility functions --------------------
    def _get_garment_images(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Returns a list of garment image paths.
        """
        images: Dict[str, Optional[str]] = {}
        garment_ids, _ = parse_outfit_fields(current_outfit)

        for garment_id in garment_ids:
            if str(garment_id).startswith("U"):
                continue
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
                images[garment_id] = image_path

        return images

    def _get_garment_images_types(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Get category information for all garment images in the outfit.
        The returned list order corresponds to the image path list returned by _get_garment_images.

        Returns:
            List[str]: List of type category information for each garment image
        """
        types: Dict[str, Optional[str]] = {}
        garment_ids, _ = parse_outfit_fields(current_outfit)

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
                garment_type = garment_info.get("type", "")
                types[garment_id] = garment_type

        return types

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

    def _get_edited_look_image(self, outfit_id: str) -> Optional[str]:
        """
        Get edited look image path.
        """
        image = os.path.join(
            self.look_edited_root,
            str(outfit_id) + ".png",
        )
        if os.path.exists(image):
            return image
        print(f"MytheresaOutfitDataset: Edited look image not found: {image}")
        return None

    def _get_merged_mask_path(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        gender = current_outfit.get("gender", "unknown")
        path = get_merged_mask_v3_path(self.mask_v3_root, gender, outfit_id)
        if path:
            return path
        path = os.path.join(self.dataset_root, self.source, "annotations", "mask-sam3-resized", gender, str(outfit_id), "merged_mask.png")
        return path if os.path.isfile(path) else None

    def _get_ootd_image(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        """
        Get OOTD image path.
        """
        gender = current_outfit.get("gender", "unknown")
        gender_dir = os.path.join(self.ootd_root, gender)
        image = os.path.join(gender_dir, str(outfit_id) + ".png")
        if os.path.exists(image):
            return image
        print(f"MytheresaOutfitDataset: OOTD image not found: {image}")
        return None

    # -------------------- Dataset interface --------------------
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        outfit_id = self.samples[idx]
        current_outfit = self.outfit_data[outfit_id]

        garment_image_paths = self._get_garment_images(current_outfit)
        garment_image_types = self._get_garment_images_types(current_outfit)
        look_image_path = self._get_look_image(current_outfit, outfit_id)
        edited_look_image_path = self._get_edited_look_image(outfit_id)
        merged_mask_path = self._get_merged_mask_path(current_outfit, outfit_id)
        ootd_image_path = self._get_ootd_image(current_outfit, outfit_id)
        outfit_ids, outfit_all = parse_outfit_fields(current_outfit)
        outfit = [garment_id for garment_id in outfit_ids if garment_id in garment_image_paths]

        return {
            "outfit_id": outfit_id,
            "source": self.source,
            "gender": current_outfit.get("gender", "N/A"),
            "is_official_look": current_outfit.get("is_official_look", False),
            "is_official_outfit": current_outfit.get("is_official_outfit", False),
            "section": current_outfit.get("section", "N/A"),
            "outfit_info": current_outfit.get("outfit_info", {}),
            "garment_image_paths": garment_image_paths,
            "garment_image_types": garment_image_types,
            "look_image_path": look_image_path,
            "merged_mask_path": merged_mask_path,
            "edited_look_image_path": edited_look_image_path,
            "ootd_image_path": ootd_image_path,
            "outfit_all": outfit_all,
            "outfit": outfit,
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
            dataset_root: Root directory of the dataset
            section: Dataset split to use, can be "train" or "test", None means no filtering
        """
        self.dataset_root = dataset_root
        self.source = "polyvore"
        self.section = section

        # Build all paths based on root directory
        self.image_json = os.path.join(dataset_root, "polyvore_image_v1.0_2512.json")
        self.outfit_json = os.path.join(dataset_root, "polyvore_outfit_v1.1_2512.json")
        if not os.path.isfile(self.outfit_json):
            self.outfit_json = os.path.join(dataset_root, "polyvore_outfit_v1.0_2512.json")
        self.garment_root = os.path.join(dataset_root, "polyvore", "images")
        self.look_root = os.path.join(dataset_root, "polyvore", "looks-resized")
        self.look_edited_root = os.path.join(dataset_root, "polyvore", "edited", "banana")
        self.mask_v3_root = os.path.join(
            dataset_root, "polyvore", "annotations", "mask-v3-look-resized"
        )
        self.ootd_root = os.path.join(dataset_root, "polyvore", "ootd")
        with open(self.image_json, "r", encoding="utf-8") as f:
            self.image_data: Dict[str, Any] = json.load(f)
        with open(self.outfit_json, "r", encoding="utf-8") as f:
            self.outfit_data: Dict[str, Any] = json.load(f)

        self.samples: List[str] = []
        for outfit_id, current_outfit in self.outfit_data.items():
            # 如果指定了 section，则只保留匹配的样本
            if self.section is not None:
                outfit_section = current_outfit.get("section")
                if outfit_section != self.section:
                    continue

            # 检查必需的文件是否存在
            garment_image_paths = self._get_garment_images(current_outfit)
            look_image_path = self._get_look_image(current_outfit, outfit_id)

            if garment_image_paths and look_image_path:
                self.samples.append(outfit_id)

        section_info = f" (section={self.section})" if self.section is not None else ""
        print(f"PolyvoreOutfitDataset: Found {len(self.samples)} valid samples{section_info}")


    # -------------------- Internal utility functions --------------------
    def _get_garment_images(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        images: Dict[str, Optional[str]] = {}
        garment_ids, _ = parse_outfit_fields(current_outfit)
        gender = current_outfit.get("gender", "unknown")

        for garment_id in garment_ids:
            if str(garment_id).startswith("U"):
                continue
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
                images[garment_id] = image_path

        return images

    def _get_garment_images_types(self, current_outfit: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Get category information for all garment images in the outfit.
        The returned list order corresponds to the image path list returned by _get_garment_images.

        Returns:
            Dict[str, Optional[str]]: Dict of type category information for each garment image
        """
        types: Dict[str, Optional[str]] = {}
        garment_ids, _ = parse_outfit_fields(current_outfit)
        gender = current_outfit.get("gender", "unknown")

        for garment_id in garment_ids:
            if str(garment_id).startswith("U"):
                continue
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

        return types

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

    def _get_edited_look_image(self, outfit_id: str) -> Optional[str]:
        """
        Get edited look image path.
        """
        image = os.path.join(
            self.look_edited_root,
            str(outfit_id) + ".png",
        )
        if os.path.exists(image):
            return image
        print(f"PolyvoreOutfitDataset: Edited look image not found: {image}")
        return None

    def _get_merged_mask_path(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        gender = current_outfit.get("gender", "unknown")
        path = get_merged_mask_v3_path(self.mask_v3_root, gender, outfit_id)
        if path:
            return path
        path = os.path.join(self.dataset_root, self.source, "annotations", "mask-sam3-resized", gender, str(outfit_id), "merged_mask.png")
        return path if os.path.isfile(path) else None

    def _get_ootd_image(self, current_outfit: Dict[str, Any], outfit_id: str) -> Optional[str]:
        """
        Get OOTD image path.
        """
        gender = current_outfit.get("gender", "unknown")
        gender_dir = os.path.join(self.ootd_root, gender)
        image = os.path.join(gender_dir, str(outfit_id) + ".png")
        if os.path.exists(image):
            return image
        print(f"PolyvoreOutfitDataset: OOTD image not found: {image}")
        return None

    # -------------------- Dataset interface --------------------
    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        outfit_id = self.samples[idx]
        current_outfit = self.outfit_data[outfit_id]

        garment_image_paths = self._get_garment_images(current_outfit)
        garment_image_types = self._get_garment_images_types(current_outfit)
        look_image_path = self._get_look_image(current_outfit, outfit_id)
        edited_look_image_path = self._get_edited_look_image(outfit_id)
        merged_mask_path = self._get_merged_mask_path(current_outfit, outfit_id)
        ootd_image_path = self._get_ootd_image(current_outfit, outfit_id)
        outfit_ids, outfit_all = parse_outfit_fields(current_outfit)
        outfit = [garment_id for garment_id in outfit_ids if garment_id in garment_image_paths]

        return {
            "outfit_id": outfit_id,
            "source": self.source,
            "gender": current_outfit.get("gender", "N/A"),
            "is_official_look": current_outfit.get("is_official_look", False),
            "is_official_outfit": current_outfit.get("is_official_outfit", False),
            "section": current_outfit.get("section", "N/A"),
            "outfit_info": current_outfit.get("outfit_info", {}),
            "garment_image_paths": garment_image_paths,
            "garment_image_types": garment_image_types,
            "look_image_path": look_image_path,
            "merged_mask_path": merged_mask_path,
            "edited_look_image_path": edited_look_image_path,
            "ootd_image_path": ootd_image_path,
            "outfit_all": outfit_all,
            "outfit": outfit,
        }
