import pdfplumber
import pandas as pd
import json
import re
from pathlib import Path


# --------------------------------------------------
# BASIC TEXT NORMALIZER
# --------------------------------------------------
def normalize(text):
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("---", "")
    return text.strip()


# --------------------------------------------------
# PARSE ONE SIDE (LEFT or RIGHT)
# --------------------------------------------------
def parse_side(df, side, section):
    results = []
    current_item = None
    current_desc = None

    for _, row in df.iterrows():
        item = normalize(row["Item"])
        desc = normalize(row["Description"])
        part_no = normalize(row["Part no"])
        qty = normalize(row["Qty"])
        material = normalize(row.get("[Mtl]", ""))

        # New item starts
        if item.isdigit():
            current_item = int(item)
            current_desc = desc
            variant_notes = None
        else:
            variant_notes = desc if desc else None

        if part_no:
            results.append({
                "Section": section,
                "Item": current_item if item.isdigit() else None,
                "Description": current_desc if item.isdigit() else desc,
                "Variant_Notes": variant_notes,
                "Part_No": part_no,
                "Qty": int(qty.strip("()")) if qty.strip("()").isdigit() else None,
                "Material": material.strip("[]") if material else None,
                "Side": side
            })

    return results


# --------------------------------------------------
# PROCESS ONE TABLE
# --------------------------------------------------
def process_air_section_table(table):
    section = "AIR SECTION PARTS"
    all_rows = []

    df = pd.DataFrame(table)

    # Split LEFT and RIGHT halves
    left_df = df.iloc[:, 0:5]
    right_df = df.iloc[:, 5:10]

    left_df.columns = ["Item", "Description", "Part no", "Qty", "[Mtl]"]
    right_df.columns = ["Item", "Description", "Part no", "Qty", "[Mtl]"]

    all_rows.extend(parse_side(left_df, "LEFT", section))
    all_rows.extend(parse_side(right_df, "RIGHT", section))

    return all_rows


# --------------------------------------------------
# MAIN PDF → JSON FUNCTION
# --------------------------------------------------
def pdf_to_air_section_json(pdf_path, output_dir="output"):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    final_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 3:
                    continue

                # ✅ SAFE header detection
                header_text = normalize(
                    " ".join(cell or "" for cell in table[0])
                )
                print("header_text", header_text)

                if "AIR SECTION PARTS" not in header_text:
                    continue

                extracted = process_air_section_table(table[1:])
                final_data.extend(extracted)

    output_path = output_dir / f"{Path(pdf_path).stem}_AIR_SECTION_PARTS.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)

    print(f"\n✅ JSON created: {output_path}")
    print(f"📊 Total records: {len(final_data)}")



# --------------------------------------------------
# RUN
# --------------------------------------------------
pdf_to_air_section_json("manual.pdf")
