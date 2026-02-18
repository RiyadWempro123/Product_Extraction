import pandas as pd
import re
import json


# -----------------------------
# Text Cleaning
# -----------------------------
def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # Replace smart quotes / dashes from PDF
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
       
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # Remove remaining non-ascii characters
    text = re.sub(r"[^\x00-\x7F]+", "", text)

    return text.strip()


# -----------------------------
# Main Function
# -----------------------------
def common_parts_to_json(df: pd.DataFrame):

    if df is None or df.empty:
        return []

    df = df.reset_index(drop=True)

    # -----------------------------
    # Helper functions
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
        m = re.search(r"\d+", str(val))
        return int(m.group()) if m else None

    def clean_item(val):
        if pd.isna(val):
            return None
        num = re.sub(r"[^\d]", "", str(val))
        return int(num) if num else None

    def clean_material(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        if val in ["---", ""]:
            return None
        return re.sub(r"[\[\]]", "", val).strip()

    # -----------------------------
    # Detect Header Row
    # -----------------------------
    header_idx = None

    for i in range(len(df)):
        row_text = " ".join(str(x) for x in df.iloc[i] if pd.notna(x))
        if "item" in row_text.lower() and "part" in row_text.lower():
            header_idx = i
            break

    if header_idx is None:
        return []

    header = list(df.iloc[header_idx].values)
    data = df.iloc[header_idx + 1:].values.tolist()

    # -----------------------------
    # Detect Side-by-Side Layout
    # -----------------------------
    normalized_header = [normalize(h) for h in header]
    half = len(header) // 2

    tables = []

    if half > 0 and normalized_header[:half] == normalized_header[half:]:
        left_df = pd.DataFrame([r[:half] for r in data], columns=header[:half])
        right_df = pd.DataFrame([r[half:] for r in data], columns=header[half:])
        tables = [left_df, right_df]
    else:
        tables = [pd.DataFrame(data, columns=header)]

    # -----------------------------
    # Extract Data
    # -----------------------------
    results = []

    for table_df in tables:

        table_df.columns = [normalize(c) for c in table_df.columns]

        try:
            col_item = next(c for c in table_df.columns if "item" in c)
            col_desc = next(c for c in table_df.columns if "description" in c)
            col_qty = next(c for c in table_df.columns if "qty" in c)
            col_part = next(c for c in table_df.columns if "part" in c)
            col_mtl = next(
                c for c in table_df.columns if "mtl" in c or "material" in c
            )
        except StopIteration:
            continue

        last_item = None

        for _, row in table_df.iterrows():

            item = clean_item(row[col_item])

            if item is None:
                item = last_item
            else:
                last_item = item

            part = clean_text(row[col_part])
            desc = clean_text(row[col_desc])
            qty = extract_qty(row[col_qty])
            mtl = clean_material(row[col_mtl])

            if not item or not part:
                continue

            results.append({
                "Item": item,
                "Description": desc,
                "Qty": qty,
                "Part_No": part,
                "Material": mtl
            })

    return results
