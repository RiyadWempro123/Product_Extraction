import pdfplumber
import pandas as pd
import json
from pathlib import Path

# --------------------------------------------------
# CLEAN CELL
# --------------------------------------------------
def clean(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()

# --------------------------------------------------
# EXTRACT TABLE DATAFRAME FROM PDF PAGE
# --------------------------------------------------
def extract_diaphragm_table(pdf_path, page_number):
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

        # Find DIAPHRAGM OPTIONS table
        for table in tables:
            flat_text = " ".join([clean(c) for row in table for c in row if clean(c)])
            if "DIAPHRAGM OPTIONS" in flat_text.upper():
                df = pd.DataFrame([[clean(c) for c in row] for row in table])
                df = df.replace("", pd.NA).dropna(how="all").reset_index(drop=True)
                return df

    return None

# --------------------------------------------------
# PARSE PX03P DIAPHRAGM TABLE
# --------------------------------------------------
def parse_diaphragm_df(df):
    # Find header row containing Diaphragm + Qty
    header_index = None
    for i in range(len(df)):
        row_text = " ".join(df.iloc[i].astype(str))
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

        # Controlled column mapping for PX03P
        try:
            # Diaphragm 7
            if not pd.isna(row.iloc[2]) and str(row.iloc[2]) not in ["-----", "---", ""]:
                entry["components"]["diaphragm_7"] = {
                    "part_no": row.iloc[2],
                    "qty": int(str(row.iloc[3]).replace("(", "").replace(")", "")),
                    "material": str(row.iloc[4]).replace("[", "").replace("]", "")
                }

            # Diaphragm 8
            if not pd.isna(row.iloc[5]) and str(row.iloc[5]) not in ["-----", "---", ""]:
                entry["components"]["diaphragm_8"] = {
                    "part_no": row.iloc[5],
                    "qty": int(str(row.iloc[6]).replace("(", "").replace(")", "")),
                    "material": str(row.iloc[7]).replace("[", "").replace("]", "")
                }

            # O-Ring 19
            if not pd.isna(row.iloc[8]) and str(row.iloc[8]) not in ["-----", "---", ""]:
                entry["components"]["o_ring_19"] = {
                    "part_no": row.iloc[8],
                    "qty": int(str(row.iloc[9]).replace("(", "").replace(")", "")),
                    "material": str(row.iloc[10]).replace("[", "").replace("]", "")
                }
        except IndexError:
            pass

        results.append(entry)

    return results

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def extract_px03p_diaphragm(pdf_path, page_number):
    df = extract_diaphragm_table(pdf_path, page_number)
    if df is None:
        return []

    json_data = {
        "table_name": "DIAPHRAGM OPTIONS",
        "model": "PX03P-XXS-XXX-AXXX",
        "options": parse_diaphragm_df(df)
    }

    return json_data

# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------
if __name__ == "__main__":
    PDF_FILE = "PX03P.pdf"  # <-- Replace with your PDF path
    PAGE_NUMBER = 5                 # <-- Replace with the page number of the diaphragm table

    result = extract_px03p_diaphragm(PDF_FILE, PAGE_NUMBER)
    print(json.dumps(result, indent=2))
