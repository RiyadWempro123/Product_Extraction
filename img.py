import json
import pytesseract
from PIL import Image
import re
import os

# -----------------------------
# CONFIG
# -----------------------------
IMAGE_PATH = "image.png"   # make sure path is correct
OUTPUT_JSON = "common_parts.json"

# -----------------------------
# MATERIAL MAP
# -----------------------------
MATERIAL_MAP = {
    "P": "Polypropylene",
    "SS": "Stainless Steel",
    "D": "Acetal",
    "K": "Kynar PVDF",
    "CO": "Copper"
}

# -----------------------------
# OCR + SMART PARSER
# -----------------------------
def extract_from_image(image_path):
    if not os.path.exists(image_path):
        print("❌ Image not found:", image_path)
        return None

    text = pytesseract.image_to_string(Image.open(image_path))
    lines = text.splitlines()

    parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Example OCR line:
        # 1 Rod Assembly includes seals --- 1 24028284
        match = re.match(
            r"^(\d+)\s+(.+?)\s+(---|\[?[A-Z]{1,2}\]?)\s+(\d+)\s+(\d+-?\d*)$",
            line
        )

        if not match:
            continue

        item, desc, mtl, qty, part_no = match.groups()

        mtl = mtl.replace("[", "").replace("]", "")
        material_code = None if mtl == "---" else mtl.upper()

        parts.append({
            "item": int(item),
            "description": desc.strip(),
            "material_code": material_code,
            "material": MATERIAL_MAP.get(material_code),
            "quantity": int(qty),
            "part_number": part_no
        })

    return parts if parts else None

# -----------------------------
# MAIN
# -----------------------------
def main():
    data = extract_from_image(IMAGE_PATH)

    if not data:
        print("❌ No rows matched. Showing OCR text for debugging:\n")
        print(pytesseract.image_to_string(Image.open(IMAGE_PATH)))
        raise Exception("No data extracted from image")

    output = {"common_parts": data}

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print("✅ SUCCESS! JSON generated:\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
