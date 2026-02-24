import pandas as pd
import re

def clean_material(val):
    """Clean material column"""
    if pd.isna(val) or str(val).strip() in ["---", "-----"]:
        return None
    return re.sub(r"[\[\]]", "", str(val)).strip()

def clean_qty(val):
    """Clean quantity column"""
    if pd.isna(val):
        return None
    val = re.sub(r"[()]", "", str(val))
    return int(val) if val.isdigit() else None

def extract_models(row):
    """Extract model names dynamically from a row"""
    models = []
    for val in row:
        val = str(val).strip()
        if re.match(r"PX\d", val):
            models.append(val)
    return models

def extract_manifold_json_from_dfs(dfs):
    """Extract manifold JSON from one or multiple DataFrames"""
    if isinstance(dfs, pd.DataFrame):
        dfs = [dfs]

    mainfold_list = []

    for df in dfs:
        # find header row containing 'Item'
        header_indexes = df[df.apply(
            lambda r: r.astype(str).str.contains("Item", case=False).any(),
            axis=1
        )].index.tolist()

        for i, header_idx in enumerate(header_indexes):
            header_row = df.iloc[header_idx]

            # models are usually one row above
            model_row = df.iloc[header_idx - 1]
            models = extract_models(model_row)

            if not models:
                continue

            start = header_idx + 1
            end = header_indexes[i + 1] if i + 1 < len(header_indexes) else len(df)
            table = df.iloc[start:end].reset_index(drop=True)

            current_item = None

            for _, row in table.iterrows():
                item_raw = str(row[0]).strip()

                # detect new item row
                if item_raw.isdigit():
                    current_item = int(item_raw)
                    desc = str(row[1]).strip()
                    qty = clean_qty(row[2])
                # continuation rows like (BSP) or extra description
                elif current_item and re.match(r"^\(.*\)$", item_raw):
                    desc = str(row[1]).strip() if str(row[1]).strip() else item_raw
                    qty = clean_qty(row[2])
                else:
                    continue

                # create a new JSON entry for **each description row**
                variants = {}
                col_pointer = 3
                model_index = 0

                while col_pointer + 1 < len(row) and model_index < len(models):
                    part = str(row[col_pointer]).strip()
                    material = clean_material(row[col_pointer + 1])
                    model = models[model_index]

                    if part not in ["---", "-----", "", "nan"] and material is not None:
                        variants[model] = {
                            "Part_No": part,
                            "Material": material,
                            "Qty": qty
                        }

                    col_pointer += 2
                    model_index += 1

                if variants:
                    mainfold_list.append({
                        "Item": current_item,
                        "Description": desc,
                        "Connection_Type": None,
                        "Variants": variants
                    })

    return {"mainfold": mainfold_list}

# ---------------------------
# Example usage with your df
# ---------------------------
# df_mainfold = pd.read_excel("your_file.xlsx")  # or read CSV/PDF table
# result_json = extract_manifold_json_from_dfs(df_mainfold)
# print(result_json)
