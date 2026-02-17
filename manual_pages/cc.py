import cv2
import numpy as np
from PIL import Image
import pytesseract
import matplotlib.pyplot as plt

# -------------------------
# STEP 1: Load Image
# -------------------------
img = cv2.imread("manual_pages/page_5.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Threshold to get binary image
_, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

# -------------------------
# STEP 2: Detect Horizontal & Vertical Lines
# -------------------------
scale = 15  # adjust based on table size
horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gray.shape[1]//scale, 1))
vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, gray.shape[0]//scale))

horizontal_lines = cv2.erode(binary, horizontal_kernel, iterations=1)
horizontal_lines = cv2.dilate(horizontal_lines, horizontal_kernel, iterations=1)

vertical_lines = cv2.erode(binary, vertical_kernel, iterations=1)
vertical_lines = cv2.dilate(vertical_lines, vertical_kernel, iterations=1)

# Combine lines to get table mask
table_mask = cv2.add(horizontal_lines, vertical_lines)

# -------------------------
# STEP 3: Find Table Contours
# -------------------------
contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

table_boxes = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 100 and h > 50:  # filter small boxes
        table_boxes.append((x, y, w, h))

# -------------------------
# STEP 4: Select Tables Containing "COMMON PARTS"
# -------------------------
filtered_tables = []

for x, y, w, h in table_boxes:
    cropped_table = img[y:y+h, x:x+w]
    # OCR on cropped table
    table_text = pytesseract.image_to_string(Image.fromarray(cropped_table), config="--psm 6")
    if "COMMON PARTS" in table_text.upper():
        filtered_tables.append(cropped_table)

print(f"✅ Found {len(filtered_tables)} table(s) containing 'COMMON PARTS'.")

# -------------------------
# STEP 5: Optional - Display Selected Tables
# -------------------------
for i, tbl in enumerate(filtered_tables):
    plt.figure(figsize=(10, 4))
    plt.imshow(cv2.cvtColor(tbl, cv2.COLOR_BGR2RGB))
    plt.title(f"COMMON PARTS Table {i+1}")
    plt.axis("off")
    plt.show()

# -------------------------
# STEP 6: Extract Text for JSON
# -------------------------
all_tables_text = []
for tbl in filtered_tables:
    text = pytesseract.image_to_string(Image.fromarray(tbl), config="--psm 6")
    all_tables_text.append(text)

# Example: save as JSON
import json
json_data = {
    "common_parts_tables_text": all_tables_text,
    "source": "Page 5 of manual"
}

with open("common_parts_tables.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print("✅ Saved OCR text of COMMON PARTS tables to JSON.")
