import pdfplumber
import json
import re
from pathlib import Path

PDF_PATH = "PX01X.pdf"
OUTPUT_JSON = "common_parts.json"


def parse_part_no(text):
    """
    Extract part number and material code from:
    97122 [SS]
    """
    match = re.search(r"(\d+)\s*\[([A-Z]+)\]", text)
    if match:
        return match.group(1), match.group(2)
    return text.strip(), None


def extract_common_parts(pdf_path):
    results = []
    capture = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # Start extraction at COMMON PARTS
            if "COMMON PARTS" in text:
                capture = True

            if not capture:
                continue

            words = page.extract_words(
                use_text_flow=True,
                keep_blank_chars=False
            )

            # Group words by line (y-position)
            lines = {}
            for w in words:
                y = round(w["top"], 1)
                lines.setdefault(y, []).append(w)

            for y, row in lines.items():
                row_text = " ".join(w["text"] for w in row)

                # Stop when next section starts
                if "MANIFOLD / FLUID CAP OPTIONS" in row_text:
                    return results

                # Skip headers
                if not re.match(r"^\d+", row_text):
                    continue

                # Column detection by X position
                item = description = qty = part_text = ""

                for w in row:
                    x = w["x0"]
                    if x < 50:
                        item += w["text"]
                    elif 50 <= x < 260:
                        description += " " + w["text"]
                    elif 260 <= x < 330:
                        qty += w["text"]
                    else:
                        part_text += " " + w["text"]

                part_no, material = parse_part_no(part_text)

                results.append({
                    "item": item.strip(),
                    "description": description.strip(),
                    "qty": qty.strip().strip("()"),
                    "part_no": part_no,
                    "material": material
                })

    return results


if __name__ == "__main__":
    data = extract_common_parts(PDF_PATH)

    Path(OUTPUT_JSON).write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    print(f"✅ Extracted {len(data)} COMMON PARTS")
