"""Render OOTD, paired inputs/outputs, and full-width task prompts."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--example-dir", type=Path, default=Path("examples"))
    args = p.parse_args()
    labels = [("OOTD", "ootd.png"),
              ("Input origin (inpainting)", "input-inpainting.png"),
              ("Output inpainting", "output-inpainting.png"),
              ("Input origin (editing)", "input-editing.png"),
              ("Output editing", "output-editing.png")]
    w, h, header, footer = 700, 1050, 70, 145
    canvas = Image.new("RGB", (w*5, h+header+footer), "white")
    draw = ImageDraw.Draw(canvas)
    for idx, (label, filename) in enumerate(labels):
        with Image.open(args.example_dir/filename) as source:
            im = ImageOps.contain(source.convert("RGB"), (w-24, h-24))
        canvas.paste(im, (idx*w+(w-im.width)//2, header+(h-im.height)//2))
        draw.text((idx*w+w//2, header//2), label, font=font(30), fill="black", anchor="mm")
    prompts = ["Inpainting: " + (args.example_dir/"prompt-inpainting.txt").read_text().strip(),
               "Editing: " + (args.example_dir/"prompt-editing.txt").read_text().strip()]
    size = 25
    while size > 10 and any(draw.textlength(text, font=font(size)) > w*5-48 for text in prompts):
        size -= 1
    for idx, text in enumerate(prompts):
        draw.text((24, header+h+30+idx*55), text, font=font(size), fill="black")
    canvas.save(args.example_dir/"comparison.jpg", quality=97)
    canvas.save(args.example_dir/"comparison.png")


if __name__ == "__main__":
    main()
