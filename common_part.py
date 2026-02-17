import pdfplumber
import re
import json
import cv2
import numpy as np
import easyocr

PDF_PATH = "PX03P.pdf"
OUTPUT_JSON = "common_parts.json"

def parse_part(text):
    """
    Extract part number and material from:
    97122 [SS] or 23981632 [ P ]
    """
    m = re.search(r"(\d+)\s*\[\s*([A-Z]+)\s*\]", text)
    if m:
        return m.group(1), m.group(2)
    return None, None

def extract_common_parts_pdfplumber(pdf_path):
    """Try extracting COMMON PARTS using pdfplumber (text PDF)."""
    results = []
    capture = False
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # Check for section start
            if re.search(r"COMMON\s+PARTS", text, re.IGNORECASE):
                capture = True

            if not capture:
                continue

            # Get words with coordinates
            words = page.extract_words(use_text_flow=True)
            if not words:
                continue

            rows = {}
            for w in words:
                y = int(round(w["top"]))
                rows.setdefault(y, []).append(w)

            for y in sorted(rows):
                row = rows[y]
                row_text = " ".join(w["text"] for w in row)

                # Optional: stop at next section
                if re.search(r"MANIFOLD\s*/\s*FLUID CAP OPTIONS", row_text, re.IGNORECASE):
                    return results

                # Row must start with item number
                if not re.match(r"^\d+\b", row_text):
                    continue

                # Split row into columns (roughly by x-position)
                item = desc = qty = part_txt = ""
                for w in row:
                    x = w["x0"]
                    txt = w["text"]
                    if x < 50:
                        item += txt
                    elif 50 <= x < 260:
                        desc += " " + txt
                    elif 260 <= x < 330:
                        qty += txt
                    else:
                        part_txt += " " + txt

                part_no, material = parse_part(part_txt)
                if not item.strip().isdigit() or not part_no or not material:
                    continue

                key = (item.strip(), part_no)
                if key in seen:
                    continue
                seen.add(key)

                results.append({
                    "item": item.strip(),
                    "description": desc.strip(),
                    "qty": qty.strip().strip("()"),
                    "part_no": part_no,
                    "material": material
                })
    return results

def extract_common_parts_ocr(pdf_path):
    """Fallback: use OCR + table detection if pdfplumber fails."""
    results = []
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Convert each PDF page to image
    import pdf2image
    pages = pdf2image.convert_from_path(pdf_path, dpi=300)

    for page_num, img in enumerate(pages):
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # OCR detection
        ocr_results = reader.readtext(gray)

        # Simple heuristic: look for COMMON PARTS section
        capture = False
        seen = set()
        for bbox, text, conf in ocr_results:
            if re.search(r"COMMON\s+PARTS", text, re.IGNORECASE):
                capture = True
                continue
            if not capture:
                continue
            if re.search(r"MANIFOLD\s*/\s*FLUID CAP OPTIONS", text, re.IGNORECASE):
                break

            # Extract item, description, qty, part
            m = re.match(r"(\d+)\s+(.*?)\s+(\d+)\s+(.*)", text)
            if m:
                item, desc, qty, part_txt = m.groups()
                part_no, material = parse_part(part_txt)
                if part_no and material:
                    key = (item, part_no)
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            "item": item,
                            "description": desc.strip(),
                            "qty": qty.strip(),
                            "part_no": part_no,
                            "material": material
                        })
    return results

if __name__ == "__main__":
    # First try pdfplumber
    data = extract_common_parts_pdfplumber(PDF_PATH)
    if not data:
        print("⚠️ pdfplumber failed, falling back to OCR...")
        data = extract_common_parts_ocr(PDF_PATH)

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Extracted {len(data)} COMMON PARTS")
    print(json.dumps(data, indent=2))
