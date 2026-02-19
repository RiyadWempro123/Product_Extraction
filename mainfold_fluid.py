import pandas as pd
import re

def extract_manifold_json_from_dfs(dfs):

    if isinstance(dfs, pd.DataFrame):
        dfs = [dfs]

    final_items = {}

    for df in dfs:

        # Detect header rows (where "Item" exists)
        header_indexes = df[df.apply(
            lambda row: row.astype(str).str.contains("Item", case=False).any(),
            axis=1
        )].index.tolist()

        for i in range(len(header_indexes)):

            header_row_index = header_indexes[i]
            header_row = df.iloc[header_row_index]

            # 🔥 Model names are usually TWO rows above "Item"
            model_row_index = header_row_index - 1
            if model_row_index < 0:
                continue

            model_row = df.iloc[model_row_index]

            # Extract model names dynamically
            model_names = []
            for val in model_row:
                val = str(val).strip()
                if val.upper().startswith("PX"):
                    model_names.append(val)

            if not model_names:
                continue

            # Determine table range
            start = header_row_index + 1
            end = header_indexes[i + 1] if i + 1 < len(header_indexes) else len(df)
            table_df = df.iloc[start:end].reset_index(drop=True)

            current_item = None

            for _, row in table_df.iterrows():

                item_raw = str(row[0]).strip()

                # Detect new item row
                if item_raw.isdigit():
                    current_item = int(item_raw)
                    description = str(row[1]).strip()

                    # Clean Qty column (single qty)
                    qty_raw = str(row[2]).strip()
                    qty_clean = re.sub(r"[()]", "", qty_raw)
                    qty_clean = int(qty_clean) if qty_clean.isdigit() else None

                    if current_item not in final_items:
                        final_items[current_item] = {
                            "Item": current_item,
                            "Description": description,
                            "Connection_Type": None,
                            "Variants": {}
                        }

                # Continuation row like "(BSP)"
                elif current_item and item_raw.startswith("("):
                    description = final_items[current_item]["Description"] + " " + item_raw
                    qty_raw = str(row[2]).strip()
                    qty_clean = re.sub(r"[()]", "", qty_raw)
                    qty_clean = int(qty_clean) if qty_clean.isdigit() else None
                else:
                    continue

                # 🔥 Now dynamically extract variants
                # After Qty column, pattern is:
                # PartNo, [Mtl], PartNo, [Mtl], ...
                col_pointer = 3

                model_index = 0

                while col_pointer + 1 < len(row) and model_index < len(model_names):

                    part_no = str(row[col_pointer]).strip()
                    material = str(row[col_pointer + 1]).strip()

                    col_pointer += 2
                    model = model_names[model_index]
                    model_index += 1

                    if part_no in ["-----", "---", "nan"]:
                        continue

                    material_clean = re.sub(r"[\[\]]", "", material)

                    final_items[current_item]["Variants"][model] = {
                        "Part_No": part_no,
                        "Material": material_clean,
                        "Qty": qty_clean
                    }
    print("Final_items", final_items)
    return {"mainfold": list(final_items.values())}
