import pdfplumber
import pandas as pd
from pathlib import Path
import json
import re

# -----------------------------
# CONFIG
# -----------------------------
pdf_path = "PX03P.pdf"  # your PDF file
output_dir = Path("output_tables")
output_dir.mkdir(exist_ok=True)
PAGE_NUMBER = 5  # target page

# -----------------------------
# HELPER FUNCTION
# -----------------------------
def clean_parts_table(df):
    clean_rows = []
    for idx, row in df.iterrows():
        row = row.fillna("").astype(str)

        # Skip header or empty rows
        if any("Item" in x for x in row.values) or all(not x.strip() for x in row.values):
            continue

        # Clean Item: remove leading bullets/unwanted symbols
        item = row.get('Item', '').strip()
        item = re.sub(r"^[^\d]*", "", item)  # remove only leading non-digit characters

        # Description
        desc = row.get('Description (size)', '').strip()

        # Qty: remove parentheses, extract digits
        qty_raw = row.get('Qty', '').strip()
        qty_match = re.search(r"\d+", qty_raw)
        qty = int(qty_match.group()) if qty_match else None

        # Part number
        part_no = row.get('Part No.', '').strip()

        # Material: remove brackets
        mtl = row.get('Mtl', '').strip()
        mtl = re.sub(r"[\[\]]", "", mtl) if mtl else None

        # Only add row if essential info exists
        if item and qty and part_no:
            clean_rows.append({
                "Item": int(item),
                "Description": desc,
                "Qty": qty,
                "Part_No": part_no,
                "Material": mtl
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
        page = pdf.pages[PAGE_NUMBER - 1]  # zero-based index
        tables = page.extract_tables()
        print(f"✅ Found {len(tables)} tables on page {PAGE_NUMBER}.")

        table_count = 0
        for table_idx, table in enumerate(tables, start=1):
            if not table or len(table) < 2:
                continue

            # Check if table contains "COMMON PARTS"
            first_row_text = " ".join([str(cell) for cell in table[0]])
            if "COMMON PARTS" not in first_row_text.upper():
                continue  # skip this table

            # Create DataFrame
            raw_df = pd.DataFrame(table[1:], columns=table[0])
           
            print("raw_df", raw_df)

            raw_df.columns = [str(c).strip() if c is not None else "" for c in raw_df.columns]
            print(raw_df.columns)
     

            # Clean table
            clean_df = clean_parts_table(raw_df)
            print("Clean_df", clean_df)

            if not clean_df.empty:
                table_count += 1
                # Save CSV
                csv_path = output_dir / f"common_parts_page_{PAGE_NUMBER}_{table_count}.csv"
                clean_df.to_csv(csv_path, index=False)

                # Save JSON
                json_path = output_dir / f"common_parts_page_{PAGE_NUMBER}_{table_count}.json"
                clean_df.to_json(json_path, orient="records", indent=4, force_ascii=False)

                # Print cleaned table
                print(f"\n📄 Page {PAGE_NUMBER} – Clean COMMON PARTS (Table {table_count}):")
                print(clean_df)

print(f"\n✅ Extraction complete. {table_count} table(s) saved to '{output_dir}'")

