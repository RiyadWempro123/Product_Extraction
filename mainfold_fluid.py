import pandas as pd
import re


def clean_material(val):
    if pd.isna(val):
        return None
    return re.sub(r"[\[\]]", "", str(val)).strip()


def clean_qty(val):
    if pd.isna(val):
        return None
    val = re.sub(r"[()]", "", str(val))
    return int(val) if val.isdigit() else None


def extract_models(row):
    """
    Extract model names like PX01X-HDS
    """
    models = []
    for val in row:
        val = str(val).strip()
        if re.match(r"PX\d", val):
            models.append(val)
    return models


def extract_fluid_connection_json(df):

    final_items = {}

    # find header rows
    header_indexes = df[df.apply(
        lambda r: r.astype(str).str.contains("Item", case=False).any(),
        axis=1
    )].index.tolist()

    for i in range(len(header_indexes)):

        header_idx = header_indexes[i]

        # models are usually one row above header
        model_row = df.iloc[header_idx - 1]
        models = extract_models(model_row)

        if not models:
            continue

        start = header_idx + 1
        end = header_indexes[i+1] if i+1 < len(header_indexes) else len(df)

        table = df.iloc[start:end].reset_index(drop=True)

        for _, row in table.iterrows():

            item_raw = str(row[0]).strip()

            if not item_raw.isdigit():
                continue

            item = int(item_raw)
            desc = str(row[1]).strip()

            if item not in final_items:
                final_items[item] = {
                    "Item": item,
                    "Description": desc,
                    "Variants": {}
                }

            col = 2
            model_index = 0

            while col + 2 < len(row) and model_index < len(models):

                part = str(row[col]).strip()
                material = clean_material(row[col + 1])
                qty = clean_qty(row[col + 2])

                model = models[model_index]

                if part not in ["---", "nan", ""]:
                    final_items[item]["Variants"][model] = {
                        "Part_No": part,
                        "Material": material,
                        "Qty": qty
                    }

                col += 3
                model_index += 1

    return {"fluid_connection": list(final_items.values())}
