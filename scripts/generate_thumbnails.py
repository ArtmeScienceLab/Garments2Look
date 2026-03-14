#!/usr/bin/env python3
"""
将 dataset/<outfit_id>/images 下所有图片按 540px 高度生成缩略图，
保持相同目录结构输出到 thumbnail/<outfit_id>/images。
"""
from pathlib import Path
from PIL import Image

# 配置路径（相对于项目 public 目录）
PUBLIC = Path(__file__).resolve().parent.parent / "public"
SRC_BASE = PUBLIC / "dataset"
DST_BASE = PUBLIC / "thumbnail"
TARGET_HEIGHT = 540

# 支持的图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def resize_to_height(img: Image.Image, height: int) -> Image.Image:
    """按指定高度缩放，保持宽高比。若已更小则不放大。"""
    w, h = img.size
    if h <= height:
        return img
    ratio = height / h
    new_w = max(1, int(w * ratio))
    return img.resize((new_w, height), Image.Resampling.LANCZOS)


def process_image(src_path: Path, dst_path: Path) -> None:
    """读取图片、缩放到 540 高度、保存到目标路径。"""
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path) as img:
        img.load()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        thumb = resize_to_height(img, TARGET_HEIGHT)
        ext = dst_path.suffix.lower()
        if ext == ".png":
            thumb.save(dst_path, "PNG", optimize=True)
        elif ext == ".webp":
            thumb.save(dst_path, "WEBP", quality=88)
        else:
            thumb.save(dst_path, "JPEG", quality=88, optimize=True)


def main():
    if not SRC_BASE.is_dir():
        print(f"源目录不存在: {SRC_BASE}")
        return

    DST_BASE.mkdir(parents=True, exist_ok=True)

    # 遍历 dataset 下每个 outfit 目录（包含 images 的）
    outfit_dirs = [d for d in SRC_BASE.iterdir() if d.is_dir()]
    total = 0
    for outfit_dir in sorted(outfit_dirs):
        images_dir = outfit_dir / "images"
        if not images_dir.is_dir():
            continue

        # 递归找所有图片
        for src_path in images_dir.rglob("*"):
            if not src_path.is_file() or src_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            rel = src_path.relative_to(images_dir)
            dst_path = DST_BASE / outfit_dir.name / "images" / rel

            try:
                process_image(src_path, dst_path)
                total += 1
                print(f"  {rel}")
            except Exception as e:
                print(f"  跳过 {src_path}: {e}")

    print(f"\n完成，共生成 {total} 张缩略图，输出目录: {DST_BASE}")


if __name__ == "__main__":
    main()
