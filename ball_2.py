import pdfplumber
import pandas as pd
import json
import re
from pathlib import Path


# --------------------------------------------------
# UTILITIES
# --------------------------------------------------

def clean(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


def parse_qty(val):
    """Safely extract numeric quantity"""
    if pd.isna(val):
        return 0
    val = re.sub(r"[^\d]", "", str(val))
    return int(val) if val else 0


# --------------------------------------------------
# EXTRACT TABLE FROM PDF PAGE
# --------------------------------------------------

def extract_table_from_pdf(pdf_path, page_number, keyword):
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

        for table in tables:
            flat_text = " ".join(
                clean(cell)
                for row in table
                for cell in row
                if clean(cell)
            )

            if keyword.upper() in flat_text.upper():
                df = pd.DataFrame([[clean(c) for c in row] for row in table])
                df = df.replace("", pd.NA).dropna(how="all").reset_index(drop=True)
                return df

    return None


# --------------------------------------------------
# UNIVERSAL OPTION PARSER (BALL / DUCKBILL / BALL ONLY)
# --------------------------------------------------

def parse_option_table(df):

    result = {
        "table_name": "",
        "options": []
    }

    # Detect table type from first row
    first_row_text = " ".join(df.iloc[0].astype(str)).upper()

    if "BALL / DUCKBILL OPTIONS" in first_row_text:
        result["table_name"] = "BALL / DUCKBILL OPTIONS"
    elif "BALL OPTIONS" in first_row_text:
        result["table_name"] = "BALL OPTIONS"
    else:
        result["table_name"] = "UNKNOWN OPTIONS"

    # Find header row containing "Ball" and "Qty"
    header_index = None
    for i, row in df.iterrows():
        row_text = " ".join(row.astype(str))
        if "Ball" in row_text and "Qty" in row_text:
            header_index = i
            break

    if header_index is None:
        return result

    data_df = df.iloc[header_index + 1:].reset_index(drop=True)

    # Process each row dynamically
    for _, row in data_df.iterrows():

        row_values = [clean(v) for v in row]

        # Find all option codes dynamically
        option_positions = [
            i for i, val in enumerate(row_values)
            if isinstance(val, str) and val.startswith("-")
        ]

        for pos in option_positions:
            try:
                part_no = row_values[pos + 1]
                qty = parse_qty(row_values[pos + 2])
                material = row_values[pos + 3].replace("[", "").replace("]", "")

                if part_no in ["---", "-----", "", None]:
                    continue

                result["options"].append({
                    "option_code": row_values[pos],
                    "part_no": part_no,
                    "qty": qty,
                    "material": material
                })

            except IndexError:
                continue

    return result


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def extract_options_from_pdf(pdf_path, page_number, keyword="BALL OPTIONS"):

    df = extract_table_from_pdf(pdf_path, page_number, keyword)

    if df is None:
        return {"error": "Table not found on this page"}

    return parse_option_table(df)


# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------

if __name__ == "__main__":

    PDF_FILE = "PX01X.pdf"   # Change file
    PAGE_NUMBER = 5               # Change page

    result = extract_options_from_pdf(
        PDF_FILE,
        PAGE_NUMBER,
        keyword="BALL OPTIONS"     # Or "BALL / DUCKBILL OPTIONS"
    )

    print(json.dumps(result, indent=2))
