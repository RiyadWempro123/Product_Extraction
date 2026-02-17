# import re

# def clean_text(text):
#     text = str(text)
#     text = re.sub(r"[^\x00-\x7F]+", "", text)  # remove non-ascii
#     return text.strip()

# text = """ASSEMBLY TORQUE REQUIREMENTS
# NOTE: DO NOT OVERTIGHTEN FASTENERS.
# (6) Bolt, 95 - 105 in. lbs (10.7 - 11.9 Nm).
# (26) Bolt, 50 - 60 in. lbs (5.6 - 6.8 Nm), / alternately and evenly, then retorque
# after initial run-in.
# (29) Nut, 50 - 60 in. lbs (5.6 - 6.8 Nm), / alternately and evenly, then retorque
# after initial run-in.
# LUBRICATION / SEALANTS
#  Apply Lubriplate (94276) to all “O” rings, “U” cups and mating parts.
#  Apply anti-seize compound to threads and bolt and nut flange heads
# which contact pump case when using stainless steel fasteners.
#  Apply Loctite® 242® to threads."""
# print(clean_text(text))




import pdfplumber
import pandas as pd
import json
from pathlib import Path


# --------------------------------------------------
# CLEAN TEXT
# --------------------------------------------------
def clean_text(value):
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def make_unique_columns(columns):
    seen = {}
    new_cols = []

    for col in columns:
        col = clean_text(col)
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)

    return new_cols


# --------------------------------------------------
# FIND HEADER ROW
# --------------------------------------------------
def find_header_row(df):
    for i in range(len(df)):
        row_text = " ".join(str(v) for v in df.iloc[i].values)
        if "Item" in row_text and "Part" in row_text:
            return i
    return None


# --------------------------------------------------
# CONVERT WIDE KIT TABLE TO JSON (DYNAMIC)
# --------------------------------------------------
def convert_wide_table_to_json(df):

    df = df.applymap(clean_text)

    # ---- Detect header row ----
    header_index = find_header_row(df)
    if header_index is None:
        return None  # Not a structured kit table

    # ---- Extract title ----
    kit_title = clean_text(df.iloc[0, 0])

    # ---- Extract material row & kit code row ----
    material_row = header_index - 2
    kit_code_row = header_index - 1

    materials = [v for v in df.iloc[material_row] if clean_text(v)]
    kit_codes = [v for v in df.iloc[kit_code_row] if clean_text(v)]

    # ---- Set header ----
    df.columns = make_unique_columns(df.iloc[header_index])
    df = df.iloc[header_index + 1:].reset_index(drop=True)

    # ---- Detect part/material columns dynamically ----
    part_cols = [c for c in df.columns if "Part" in c]
    mtl_cols = [c for c in df.columns if "[Mtl]" in c]

    variants = []

    for idx in range(len(part_cols)):

        variant = {
            "kit_name": kit_title,
            "kit_code": kit_codes[idx] if idx < len(kit_codes) else "",
            "material_type": materials[idx] if idx < len(materials) else "",
            "items": []
        }

        for _, row in df.iterrows():

            if not row.get("Item"):
                continue

            item_entry = {
                "item": row.get("Item"),
                "description": row.get("Description (size)"),
                "qty": row.get("Qty"),
                "part_no": row.get(part_cols[idx]),
                "material": row.get(mtl_cols[idx]) if idx < len(mtl_cols) else ""
            }

            variant["items"].append(item_entry)

        variants.append(variant)

    return variants


# --------------------------------------------------
# MAIN FUNCTION: PDF PAGE → JSON
# --------------------------------------------------
def extract_page_tables_as_json(pdf_path, page_number):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    all_json = []

    with pdfplumber.open(pdf_path) as pdf:

        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError("Invalid page number")

        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

        if not tables:
            return []

        for table in tables:

            cleaned = [[clean_text(c) for c in row] for row in table]
            df = pd.DataFrame(cleaned)

            json_result = convert_wide_table_to_json(df)

            if json_result:
                all_json.extend(json_result)

    return all_json


# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------
if __name__ == "__main__":

    PDF_FILE = "PX03P.pdf"
    PAGE_NUMBER = 5

    result = extract_page_tables_as_json(PDF_FILE, PAGE_NUMBER)

    print(json.dumps(result, indent=2, ensure_ascii=False))
