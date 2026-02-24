import pandas as pd
import re


# -----------------------------
# Cleaning helpers
# -----------------------------
def clean_material(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    val = re.sub(r"[\[\]]", "", val)
    return val if val not in ["---", "-----", ""] else None


def clean_qty(val):
    if pd.isna(val):
        return None
    val = re.sub(r"[()]", "", str(val))
    return int(val) if val.isdigit() else None


def clean_part(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val in ["---", "-----", "", "nan"]:
        return None
    return val


# -----------------------------
# Main Extraction Function
# -----------------------------
def extract_diaphragm_options(df):

    result = []

    # locate header row containing Qty / [Mtl]
    header_idx = df[df.apply(
        lambda r: r.astype(str).str.contains("Qty", case=False).any(),
        axis=1
    )].index[0]

    header = df.iloc[header_idx]

    # detect column groups dynamically
    groups = []
    i = 0
    while i < len(header):

        text = str(header[i]).lower()

        # diaphragm or o-ring block
        if "diaphragm" in text or "ring" in text or "od" in text:

            name = str(header[i]).strip()

            groups.append({
                "name": name,
                "part_col": i,
                "qty_col": i + 1,
                "mtl_col": i + 2
            })

            i += 3
        else:
            i += 1

    # data rows
    table = df.iloc[header_idx + 1:].reset_index(drop=True)

    for _, row in table.iterrows():

        model_code = str(row[0]).strip()

        if not model_code.startswith("-"):
            continue

        item = {
            "Model_Code": model_code,
            "Ball_Service_Kit": clean_part(row[1])
        }

        for g in groups:

            name = g["name"]

            part = clean_part(row[g["part_col"]])
            qty = clean_qty(row[g["qty_col"]])
            mtl = clean_material(row[g["mtl_col"]])

            key = name.replace(" ", "_")

            item[key] = {
                "Part_No": part,
                "Qty": qty,
                "Material": mtl
            }

        result.append(item)

    return {"diaphragm_options": result}
