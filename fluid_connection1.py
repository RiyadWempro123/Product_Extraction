import pdfplumber
import pandas as pd
import json
import re
from pathlib import Path


# --------------------------------------------------
# TEXT CLEANER
# --------------------------------------------------
def normalize(text):
    if text is None:
        return ""
    text = str(text).replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("---", "")
    return text.strip()


# --------------------------------------------------
# EXTRACT PARTS FROM A SINGLE TABLE
# --------------------------------------------------
def extract_parts_from_table(table, pdf_name, page_no):
    rows = []

    # Detect variant headers (PX01X-XXX)
    variant_row = table[2]
    variants = [normalize(c) for c in variant_row if c and normalize(c).startswith("PX")]

    if not variants:
        return rows

    df = pd.DataFrame(table[4:])

    for _, r in df.iterrows():
        item = normalize(r[0])
        desc = normalize(r[1])

        if not item.isdigit() or not desc:
            continue

        col = 2
        for variant in variants:
            part_no = normalize(r[col])
            material = normalize(r[col + 1])
            qty = normalize(r[col + 2])

            if part_no:
                rows.append({
                    "Page": page_no,
                    "Item": int(item),
                    "Description": desc,
                    "Variant": variant,
                    "Part_No": part_no,
                    "Material": material.strip("[]"),
                    "Qty": int(qty.strip("()")) if qty.strip("()").isdigit() else None
                })

            col += 3

    return rows


# --------------------------------------------------
# PROCESS ONE PDF (PAGE NUMBER ADDED)
# --------------------------------------------------
def pdf_to_json(pdf_path, page_numbers, output_dir="output"):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    if isinstance(page_numbers, int):
        page_numbers = [page_numbers]

    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no in page_numbers:
            page_index = page_no - 1  # zero-based index

            if page_index >= len(pdf.pages):
                continue

            page = pdf.pages[page_index]
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 5:
                    continue

                extracted = extract_parts_from_table(
                    table,
                    pdf_name=Path(pdf_path).name,
                    page_no=page_no
                )

                all_rows.extend(extracted)

    # Save single JSON
    json_path = output_dir / f"{Path(pdf_path).stem}_parts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=4)

    print(f"\n✅ JSON created: {json_path}")
    print(f"📊 Total parts extracted: {len(all_rows)}")


# --------------------------------------------------
# RUN (DEFINE TABLE PAGE HERE)
# --------------------------------------------------
pdf_to_json("manual.pdf", page_numbers=5)

