from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import re
import json
import cv2
import numpy as np

# ------------------------------
# Configuration
# ------------------------------
PDF_PATH = "manual.pdf"
DPI = 400  # high resolution for OCR
OUTPUT_JSON = "aro_parts.json"

# ------------------------------
# Step 1: Convert PDF to Images
# ------------------------------
print("Converting PDF pages to images...")
pages = convert_from_path(PDF_PATH, dpi=DPI)
print(f"Total pages: {len(pages)}")

# ------------------------------
# Step 2: OCR each page
# ------------------------------
all_text = []

for i, page in enumerate(pages, 1):
    print(f"OCR on page {i}...")
    # convert PIL image to OpenCV
    img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Optional: thresholding to improve OCR
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Run Tesseract OCR
    text = pytesseract.image_to_string(thresh)
    all_text.append(text)

# ------------------------------
# Step 3: Extract tables from OCR text
# ------------------------------
print("Parsing OCR text for Part No / Description / Qty...")
parts = []

# Simple line-based parsing
for page_text in all_text:
    lines = page_text.split("\n")
    for line in lines:
        line = line.strip()
        print("Line", line)
        if not line:
            continue

        part_no_match = re.search(r"\b\d{5,}\b", line)
        if part_no_match:
            part_no = part_no_match.group()
            qty_match = re.search(r"\(?(\d{1,3})\)?$", line)
            qty = qty_match.group(1) if qty_match else ""
            # Description = line minus part_no and qty
            description = line.replace(part_no, "").replace(qty, "").replace("()", "").strip()
            if description:
                parts.append({
                    "part_no": part_no,
                    "description": description,
                    "qty": qty
                })

# ------------------------------
# Step 4: Save structured JSON
# ------------------------------
print(f"Total parts extracted: {len(parts)}")
with open(OUTPUT_JSON, "w") as f:
    json.dump(parts, f, indent=4)

print(f"Saved → {OUTPUT_JSON}")
