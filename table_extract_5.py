import pdfplumber
import pandas as pd
from pathlib import Path
import re
import json 
# -----------------------------
# CONFIG
# -----------------------------
pdf_path = "PX03P.pdf"
output_dir = Path("output_tables")
output_dir.mkdir(exist_ok=True)
PAGE_NUMBER = 5

# -----------------------------
# HELPER FUNCTION
# -----------------------------
def clean_parts_table(df):
    clean_rows = []
    for idx, row in df.iterrows():
        row = row.fillna("").astype(str)

        # Skip empty rows
        if all(not x.strip() for x in row.values):
            continue

        # Clean Item: remove leading bullets/unwanted symbols
        item = row.get('Item', '').strip()
        item = re.sub(r"^[^\d]*", "", item)

        # Description
        desc = row.get('Description (size)', '').strip() if 'Description (size)' in row else ""

        # Qty: handle integers and floats with units like "(0.6 FT)"
        qty_raw = row.get('Qty', '').strip() if 'Qty' in row else ""
        qty_match = re.search(r"\d+(\.\d+)?", qty_raw)  # match int or float
        qty = float(qty_match.group()) if qty_match else None

        # Part number
        part_no = row.get('Part No.', '').strip() if 'Part No.' in row else ""

        # Material: remove brackets
        mtl = row.get('Mtl', '').strip() if 'Mtl' in row else ""
        mtl = re.sub(r"[\[\]]", "", mtl) if mtl else None

        # Only add row if essential info exists
        if item and qty is not None and part_no:
            clean_rows.append({
                "Item": int(item),
                "Description": desc,
                "Qty": qty,
                "Part_No": part_no,
                "Material": mtl if mtl else "Unknown"
            })

    return pd.DataFrame(clean_rows)

# -----------------------------
# MAIN EXTRACTION
# -----------------------------
with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)
    print(f"📄 PDF has {total_pages} pages.")

    if PAGE_NUMBER > total_pages:
        print(f"❌ Error: Requested page {PAGE_NUMBER} does not exist.")
    else:
        page = pdf.pages[PAGE_NUMBER - 1]
        tables = page.extract_tables()
        print(f"✅ Found {len(tables)} tables on page {PAGE_NUMBER}.")

        table_count = 0
        for table_idx, table in enumerate(tables, start=1):
            if not table or len(table) < 2:
                continue

            # Flatten first column to detect "COMMON PARTS"
            first_col_text = " ".join([str(cell) for cell in table[0]])
            if "COMMON PARTS" not in first_col_text.upper():
                continue

            # Assign header and data correctly
            print("Tables.....", table)
            header = table[1]
            data = table[2:]

            raw_df = pd.DataFrame(data, columns=header)
            raw_df.columns = [str(c).strip() for c in raw_df.columns]

            print("\nRaw DataFrame with correct columns:")
            print(raw_df)

            # Clean table
            clean_df = clean_parts_table(raw_df)
            print("clean_df", clean_df)

            if not clean_df.empty:
                # Further clean Description and Part_No
                clean_df["Description"] = clean_df["Description"].str.strip()
                clean_df["Part_No"] = clean_df["Part_No"].str.replace(r"[^\w\-]", "", regex=True)

                table_count += 1
                csv_path = output_dir / f"common_parts_page_{PAGE_NUMBER}_{table_count}.csv"
                clean_df.to_csv(csv_path, index=False)

                json_path = output_dir / f"common_parts_page_{PAGE_NUMBER}_{table_count}.json"
                clean_df.to_json(json_path, orient="records", indent=4, force_ascii=False)

                print(f"\n📄 Page {PAGE_NUMBER} – Clean COMMON PARTS (Table {table_count}):")
                print(clean_df)
                if not clean_df.empty:
                    # Optional: further clean columns
                    clean_df["Description"] = clean_df["Description"].str.strip()
                    clean_df["Part_No"] = clean_df["Part_No"].str.replace(r"[^\w\-]", "", regex=True)

                    # Save as JSON
                    json_path = output_dir / f"common_parts_page_{PAGE_NUMBER}_{table_count}.json"
                    clean_df.to_json(json_path, orient="records", indent=4, force_ascii=False)

                    # Also print JSON
                    clean_json = clean_df.to_dict(orient="records")
                    print("\n📄 Clean COMMON PARTS as JSON:")
                    print(json.dumps(clean_json, indent=4, ensure_ascii=False))

print(f"\n✅ Extraction complete. {table_count} table(s) saved to '{output_dir}'")
