import pandas as pd
import re
import json

# -----------------------------
# HELPERS
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
    """Extract numeric qty from string like '(12)'"""
    m = re.search(r"\d+(\.\d+)?", str(val))
    return float(m.group()) if m else None

def clean_item(val):
    """Remove bullets/icons and extract item number"""
    if not val:
        return None
    num = re.sub(r"[^\d]", "", str(val))
    return int(num) if num else None

def clean_material(val):
    if not val or str(val).strip() in ["---", ""]:
        return None
    return re.sub(r"[\[\]]", "", str(val)).strip()


# -----------------------------
# FIND HEADER ROW
# -----------------------------
def find_header_row(table):
    """Find row that looks like a header (has 'Item' and 'Part')"""
    for i, row in enumerate(table):
        txt = " ".join(str(c) for c in row if c)
        if "item" in txt.lower() and "part" in txt.lower():
            return i
    return None


# -----------------------------
# SPLIT SIDE-BY-SIDE TABLES
# -----------------------------
def split_table(table, header_idx):
    """Split table into left/right if side-by-side columns detected"""
    header = table[header_idx]
    data = table[header_idx + 1:]

    normalized = [normalize(h) for h in header]
    half = len(header) // 2

    # Detect repeated headers (side-by-side table)
    if half > 0 and normalized[:half] == normalized[half:]:
        left_df = pd.DataFrame([r[:half] for r in data], columns=header[:half])
        right_df = pd.DataFrame([r[half:] for r in data], columns=header[half:])
        return [left_df, right_df]

    return [pd.DataFrame(data, columns=header)]


# -----------------------------
# EXTRACT COMMON PARTS
# -----------------------------
def extract_common_parts(table):
    results = []

    header_idx = find_header_row(table)
    if header_idx is None:
        return []

    dfs = split_table(table, header_idx)

    for df in dfs:
        df.columns = [normalize(c) for c in df.columns]

        # Map columns dynamically
        try:
            col_map = {
                "item": next(c for c in df.columns if "item" in c),
                "desc": next(c for c in df.columns if "description" in c),
                "qty": next(c for c in df.columns if "qty" in c),
                "part": next(c for c in df.columns if "part" in c),
                "mtl": next(c for c in df.columns if "mtl" in c or "material" in c),
            }
        except StopIteration:
            continue

        last_item = None

        for _, row in df.iterrows():
            raw_item = row[col_map["item"]]
            item = clean_item(raw_item)

            # inherit item number if missing
            if item is None:
                item = last_item
            else:
                last_item = item

            qty = extract_qty(row[col_map["qty"]])
            part = str(row[col_map["part"]]).replace("#", "").strip()
            desc = str(row[col_map["desc"]]).strip()
            mtl = clean_material(row[col_map["mtl"]])

            # Skip invalid rows
            if not item or not part or part.lower() == "none":
                continue

            results.append({
                "Item": item,
                "Description": desc,
                "Qty": qty,
                "Part_No": part,
                "Material": mtl
            })

    return results


# -----------------------------
# EXTRACT JSON
# -----------------------------
def common_parts_to_json(table):
    table = table.tolist()
    parts = extract_common_parts(table)
    return json.dumps(parts, indent=4)


# -----------------------------
# # EXAMPLE USAGE
# # -----------------------------
# if __name__ == "__main__":

#     table_data = [
#         ['COMMON PARTS', None, None, None, None, None, None, None, None, None],
#         ['Item', 'Description (size)', 'Qty', 'Part No.', '[Mtl]', 'Item', 'Description (size)', 'Qty', 'Part No.', '[Mtl]'],
#         ['\uf08d 1', 'Connecting Rod', '(1)', '97122', '[SS]', '27', 'Bolt (1/4” - 20 x 1-1/8”)', '(12)', '96471', '[SS]'],
#         ['5', 'Diaphragm Washer', '(2)', '96556', '[GFN]', '29', 'Nut (1/4” - 20)', '(20)', '93828', '[SS]'],
#         ['26', 'Bolt (1/4” - 20 x 1-1/8”)', '(8)', '96471', '[SS]', '77', 'Logo Plate', '(2)', '93264', '[A]']
#     ]

#     json_output = common_parts_to_json(table_data)
#     print(json_output)
