import pdfplumber
import pandas as pd
import re
import json
from pathlib import Path

# ---------------- CONFIG ----------------
PDF_PATH = "EP10.pdf"
OUTPUT_DIR = Path("output_tables")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------- HELPERS ----------------

def clean_description(text):
    if not text:
        return None
    return (
        text
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )

def normalize_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def parse_qty(value):
    value = normalize_text(value)
    match = re.search(r"\((\d+)\)", value)
    return int(match.group(1)) if match else None

def parse_material(value):
    value = normalize_text(value)
    match = re.search(r"\[([A-Z]+)\]", value)
    return match.group(1) if match else None
def extract_rows_from_table(df):
    records = []

    for _, row in df.iterrows():
        for i in range(0, len(row), 5):
            try:
                raw = [normalize_text(row.iloc[i + j]) for j in range(5)]
            except IndexError:
                continue

            if not any(raw):
                continue

            item = raw[0] if raw[0].isdigit() else None
            desc = raw[1]

            qty = None
            material = None
            part_no = None

            for cell in raw:
                if "(" in cell and ")" in cell:
                    qty = parse_qty(cell)
                elif "[" in cell and "]" in cell:
                    material = parse_material(cell)
                elif re.match(r"^[A-Z0-9\-]+$", cell):
                    part_no = cell

            if not desc or not part_no:
                continue

            records.append({
                "Item": int(item) if item else None,
                "Description": clean_description(desc),
                "Qty": qty,
                "Part_No": part_no,
                "Material": material
            })
            
            

    return pd.DataFrame(records)


# ---------------- MAIN ----------------
table_count = 0

with pdfplumber.open(PDF_PATH) as pdf:
    for page_no, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()

        for table in tables:
            if not table or len(table) < 2:
                continue

            df = pd.DataFrame(table[1:], columns=table[0])
            clean_df = extract_rows_from_table(df)

            if clean_df.empty:
                continue

            table_count += 1

            # ---- Save CSV ----
            csv_path = OUTPUT_DIR / f"parts_page_{page_no}_{table_count}.csv"
            clean_df.to_csv(csv_path, index=False)

            # ---- Save JSON ----
            json_path = OUTPUT_DIR / f"parts_page_{page_no}_{table_count}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(clean_df.to_dict(orient="records"), f, indent=4)

            print(f"✅ Page {page_no} Table {table_count} saved")

print(f"\n🎉 Done! Extracted {table_count} tables.")
