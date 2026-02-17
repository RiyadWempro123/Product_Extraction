import pdfplumber
import pandas as pd
import re
from pathlib import Path
import json 
def normalize_parts_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("---", "")
    return text.strip()

PARTS_REGEX = re.compile(
    r"""
    (?P<item>\d+)?\s*
    (?P<desc>[A-Za-z ,()\-]+)
    \s*
    (\[(?P<material>[A-Z]+)\])?
    \s*
    \[(?P<qty>\d+)\]
    \s*
    (?P<part_no>[\dA-Z\-]+)
    """,
    re.VERBOSE
)

# PARTS_REGEX = re.compile(
#     r"""
#     (?P<item>\d+)?\s*
#     (?P<desc>[A-Za-z ,()\-]+)
#     \s*
#     (\[(?P<material>[A-Z]+)\])?
#     \s*
#     \[(?P<qty>\d+)\]
#     \s*
#     (?P<part_no>[\dA-Z\-]+)
#     """,
#     re.VERBOSE
# )
def clean_common_parts_table(df):
    rows = []
    buffer = ""

    for cell in df.astype(str).values.flatten():
        cell = normalize_parts_text(cell)

        if not cell:
            continue

        buffer += " " + cell
        # print("buffer....", buffer)

        match = PARTS_REGEX.search(buffer)
        if match:
            rows.append({
                "Item": int(match.group("item")) if match.group("item") else None,
                "Description": match.group("desc").strip(),
                "Material": match.group("material"),
                "Qty": int(match.group("qty")),
                "Part_No": match.group("part_no")
            })
            buffer = ""

    return pd.DataFrame(rows)

    
pdf_path = "PX03P.pdf"
output_dir = Path("output_tables")
output_dir.mkdir(exist_ok=True)
table_count = 0

with pdfplumber.open(pdf_path) as pdf:
    for page_no, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()

        for table in tables:
            if not table or len(table) < 2:
                continue

            raw_df = pd.DataFrame(table[1:], columns=table[0])
            print("df", raw_df)
            clean_df = clean_common_parts_table(raw_df)

            if not clean_df.empty:
                table_count += 1

                # ---- Save CSV ----
                csv_path = output_dir / f"common_parts_page_{page_no}_{table_count}.csv"
                clean_df.to_csv(csv_path, index=False)

                # ---- Convert to JSON ----
                json_data = clean_df.to_dict(orient="records")

                # ---- Save JSON ----
                json_path = output_dir / f"common_parts_page_{page_no}_{table_count}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)

                # ---- Print JSON ----
                print(f"\n📄 Page {page_no} – COMMON PARTS (JSON):")
                print(json.dumps(json_data, indent=4))

print(f"\n✅ Saved {table_count} COMMON PARTS tables (CSV + JSON)")
