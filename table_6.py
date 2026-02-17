import pdfplumber
import pandas as pd
import re
import json
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
PDF_PATH = "PX03P.pdf"
PAGE_NUMBER = 5
OUTPUT_DIR = Path("output_tables")
OUTPUT_DIR.mkdir(exist_ok=True)

# -----------------------------
# UTILS
# -----------------------------
def normalize_col(col):
    return (
        str(col)
        .lower()
        .replace("[", "")
        .replace("]", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
        .strip()
    )

def extract_qty(value):
    if not value:
        return None
    m = re.search(r"\d+(\.\d+)?", str(value))
    return float(m.group()) if m else None

def clean_item(value):
    return re.sub(r"[^\d]", "", str(value)) if value else None

def clean_material(value):
    if not value or value == "---":
        return None
    return re.sub(r"[\[\]]", "", value)

# -----------------------------
# DETECT HEADER ROW
# -----------------------------
def find_header_row(table):
    for i, row in enumerate(table):
        joined = " ".join(str(x) for x in row if x)
        if "item" in joined.lower() and "part" in joined.lower():
            return i
    return None

# -----------------------------
# MAIN
# -----------------------------
with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[PAGE_NUMBER - 1]
    tables = page.extract_tables()

    table_count = 0

    for table in tables:
        if not table or len(table) < 3:
            continue

        # Must contain COMMON PARTS
        if "COMMON PARTS" not in str(table[0]).upper():
            continue

        header_idx = find_header_row(table)
        if header_idx is None:
            continue

        header = table[header_idx]
        data = table[header_idx + 1 :]

        df = pd.DataFrame(data, columns=header)
        df.columns = [normalize_col(c) for c in df.columns]

        # Column mapping (VERY IMPORTANT)
        col_map = {
            "item": next((c for c in df.columns if "item" in c), None),
            "description": next((c for c in df.columns if "description" in c), None),
            "qty": next((c for c in df.columns if "qty" in c), None),
            "part_no": next((c for c in df.columns if "part" in c), None),
            "material": next((c for c in df.columns if "mtl" in c or "material" in c), None),
        }

        clean_rows = []

        for _, row in df.iterrows():
            item = clean_item(row[col_map["item"]]) if col_map["item"] else None
            desc = row[col_map["description"]] if col_map["description"] else None
            qty = extract_qty(row[col_map["qty"]]) if col_map["qty"] else None
            part_no = row[col_map["part_no"]] if col_map["part_no"] else None
            material = clean_material(row[col_map["material"]]) if col_map["material"] else None

            if item and qty is not None and part_no:
                clean_rows.append({
                    "Item": int(item),
                    "Description": str(desc).strip(),
                    "Qty": qty,
                    "Part_No": str(part_no).strip(),
                    "Material": material
                })

        if not clean_rows:
            continue

        table_count += 1
        clean_df = pd.DataFrame(clean_rows)

        # Save
        clean_df.to_json(
            OUTPUT_DIR / f"common_parts_page_{PAGE_NUMBER}_{table_count}.json",
            orient="records",
            indent=4,
            force_ascii=False
        )

        print(f"\n✅ COMMON PARTS Table {table_count}")
        print(json.dumps(clean_rows, indent=4, ensure_ascii=False))

print(f"\n🎉 DONE — {table_count} table(s) extracted successfully")
