import pdfplumber
import pandas as pd
import json
from pathlib import Path
import re

# --------------------------------------------------
# CLEAN CELL
# --------------------------------------------------
def clean(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()

def parse_qty(val):
    """Safely parse quantity, return 0 if invalid"""
    if pd.isna(val):
        return 0
    val = str(val).strip()
    val = re.sub(r"[^\d]", "", val)  # Remove anything that's not a digit
    if val == "":
        return 0
    return int(val)

# --------------------------------------------------
# EXTRACT TABLE DATAFRAME FROM PDF PAGE
# --------------------------------------------------
def extract_table(pdf_path, page_number, keyword="DIAPHRAGM OPTIONS"):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError("Invalid page number")
        
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()
        if not tables:
            return None

        # Find table containing keyword
        for table in tables:
            flat_text = " ".join([clean(c) for row in table for c in row if clean(c)])
            if keyword.upper() in flat_text.upper():
                df = pd.DataFrame([[clean(c) for c in row] for row in table])
                df = df.replace("", pd.NA).dropna(how="all").reset_index(drop=True)
                return df
    return None

# --------------------------------------------------
# PARSE DIAPHRAGM TABLE
# --------------------------------------------------
def parse_diaphragm_df(df):
    # Detect header row dynamically
    header_index = None
    for i, row in df.iterrows():
        row_text = " ".join(row.astype(str))
        if "Diaphragm" in row_text and "Qty" in row_text:
            header_index = i
            break
    if header_index is None:
        return []

    df.columns = df.iloc[header_index]
    df = df.iloc[header_index + 1:].reset_index(drop=True)

    results = []

    for _, row in df.iterrows():
        option_code = str(row.iloc[0]).strip()
        if not option_code.startswith("-"):
            continue

        entry = {
            "option_code": option_code,
            "service_kit": row.iloc[1],
            "components": {}
        }

        # Dynamically parse all component sets (every 3 or 4 columns after header)
        col_idx = 2
        while col_idx < len(row):
            part_no = row.iloc[col_idx]
            if pd.isna(part_no) or str(part_no).strip() in ["-----", "---", ""]:
                col_idx += 3  # Skip this set
                continue

            try:
                qty = parse_qty(row.iloc[col_idx + 1])
                material = str(row.iloc[col_idx + 2]).replace("[", "").replace("]", "")
                # Name the component dynamically
                comp_name = f"component_{len(entry['components']) + 1}"
                entry["components"][comp_name] = {
                    "part_no": part_no,
                    "qty": qty,
                    "material": material
                }
            except IndexError:
                break  # End of row

            col_idx += 3

        results.append(entry)

    return results

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def extract_diaphragm_options(pdf_path, page_number):
    df = extract_table(pdf_path, page_number)
    if df is None:
        return []

    json_data = {
        "table_name": "DIAPHRAGM OPTIONS",
        "options": parse_diaphragm_df(df)
    }

    return json_data

# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------
if __name__ == "__main__":
    PDF_FILE = "PX03P.pdf"  # Replace with your PDF
    PAGE_NUMBER = 5                 # Replace with actual page number

    result = extract_diaphragm_options(PDF_FILE, PAGE_NUMBER)
    print(json.dumps(result, indent=2))
