import pdfplumber
import pandas as pd
import re
import json
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
PDF_PATH = "EP10.pdf"
PAGE_NUMBER = 28
OUTPUT_DIR = Path("output_tables")
OUTPUT_DIR.mkdir(exist_ok=True)

# -----------------------------
# UTILS
# -----------------------------
def normalize(col):
    return (
        str(col).lower()
        .replace("[", "")
        .replace("]", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
        .strip()
    )

def extract_qty(val):
    """
    Extract numeric qty.
    Returns None for symbols like (), (†), etc.
    """
    m = re.search(r"\d+(\.\d+)?", str(val))
    return float(m.group()) if m else None

def clean_item(val):
    """
    Remove bullets/icons and extract item number.
    """
    if not val:
        return None
    num = re.sub(r"[^\d]", "", str(val))
    return int(num) if num else None

def clean_material(val):
    if not val or str(val).strip() == "---": 
        return None
    return re.sub(r"[\[\]]", "", str(val)).strip()

def find_header_row(table):
    """
    Find the row that looks like a header.
    """
    for i, row in enumerate(table):
        txt = " ".join(str(c) for c in row if c)
        if "item" in txt.lower() and "part" in txt.lower():
            print("item", i )
            return i
        
    return None

# -----------------------------
# SPLIT SIDE-BY-SIDE TABLES
# -----------------------------
def split_table(table, header_idx):
    header = table[header_idx]
    data = table[header_idx + 1 :]

    normalized = [normalize(h) for h in header]
    half = len(header) // 2

    # detect repeated headers (side-by-side)
    if half > 0 and normalized[:half] == normalized[half:]:
        return [
            pd.DataFrame([r[:half] for r in data], columns=header[:half]),
            pd.DataFrame([r[half:] for r in data], columns=header[half:])
        ]

    return [pd.DataFrame(data, columns=header)]

# -----------------------------
# MAIN EXTRACTION
# -----------------------------
all_parts = []

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[PAGE_NUMBER - 1]
    tables = page.extract_tables()

    for table in tables:
        if not table:
            continue

        # Must be COMMON PARTS table
        if "COMMON PARTS" not in str(table[0]).upper():
            continue

        print("\n📄 TABLE FOUND:")
        print(table)

        header_idx = find_header_row(table)
        if header_idx is None:
            continue

        dfs = split_table(table, header_idx)

        for df in dfs:
            df.columns = [normalize(c) for c in df.columns]

            # Flexible column mapping
            col_map = {
                "item": next(c for c in df.columns if "item" in c),
                "desc": next(c for c in df.columns if "description" in c),
                "qty": next(c for c in df.columns if "qty" in c),
                "part": next(c for c in df.columns if "part" in c),
                "mtl": next(c for c in df.columns if "mtl" in c or "material" in c),
            }

            last_item = None

            for _, row in df.iterrows():
                raw_item = row[col_map["item"]]
                item = clean_item(raw_item)

                # inherit item for continuation rows
                if item is None:
                    item = last_item
                else:
                    last_item = item

                qty = extract_qty(row[col_map["qty"]])
                part = str(row[col_map["part"]]).replace("#", "").strip()
                desc = str(row[col_map["desc"]]).strip()
                mtl = clean_material(row[col_map["mtl"]])
                

                # ✅ KEEP ROW EVEN IF QTY IS MISSING
                if item and part:
                    all_parts.append({
                        "Item": item,
                        "Description": desc,
                        "Qty": qty,           # may be None
                        "Part_No": part,
                        "Material": mtl
                    })

# -----------------------------
# SAVE OUTPUT
# -----------------------------
out = OUTPUT_DIR / f"common_parts_page_{PAGE_NUMBER}.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(all_parts, f, indent=4, ensure_ascii=False)

print("\n✅ FINAL JSON OUTPUT:")
print(json.dumps(all_parts, indent=4, ensure_ascii=False))
print(f"\n Saved to {out}")
