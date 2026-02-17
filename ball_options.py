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
    if pd.isna(val):
        return 0
    val = re.sub(r"[^\d]", "", str(val))
    return int(val) if val else 0


# --------------------------------------------------
# EXTRACT TABLE FROM PDF PAGE
# --------------------------------------------------

def extract_table_from_pdf(pdf_path, page_number):

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
            ).upper()

            # Accept only BALL option tables
            if "BALL" in flat_text and "OPTIONS" in flat_text:
                df = pd.DataFrame([[clean(c) for c in row] for row in table])
                df = df.replace("", pd.NA).dropna(how="all").reset_index(drop=True)
                return df

    return None


# --------------------------------------------------
# UNIVERSAL BALL OPTION PARSER
# (BALL / DUCKBILL / FLEX CHECK)
# --------------------------------------------------

def parse_ball_table(df):

    result = {
        "table_name": "",
        "ball_options": [],
        "secondary_options": []
    }

    # -----------------------------
    # Detect table type
    # -----------------------------
    first_row_text = " ".join(df.iloc[0].astype(str)).upper()

    if "FLEX CHECK" in first_row_text:
        result["table_name"] = "BALL / FLEX CHECK OPTIONS"
        secondary_name = "flex_check_options"
    elif "DUCKBILL" in first_row_text:
        result["table_name"] = "BALL / DUCKBILL OPTIONS"
        secondary_name = "duckbill_options"
    else:
        result["table_name"] = "BALL OPTIONS"
        secondary_name = None

    # -----------------------------
    # Find header row
    # -----------------------------
    header_index = None
    for i, row in df.iterrows():
        row_text = " ".join(row.astype(str)).upper()
        if "BALL" in row_text and "QTY" in row_text:
            header_index = i
            break

    if header_index is None:
        return result

    data_df = df.iloc[header_index + 1:].reset_index(drop=True)

    # -----------------------------
    # Parse rows
    # -----------------------------
    for _, row in data_df.iterrows():

        row_text = " ".join(row.astype(str)).upper()

        # 🔴 Stop when SEAT OPTIONS section starts
        if "SEAT OPTIONS" in row_text:
            break

        # Skip random seat header rows
        if "SEAT" in row_text and "OPTIONS" in row_text:
            continue

        row_values = [clean(v) for v in row]

        option_positions = [
            i for i, val in enumerate(row_values)
            if isinstance(val, str) and val.startswith("-")
        ]

        for idx, pos in enumerate(option_positions):

            try:
                part_no = row_values[pos + 1]
                qty = parse_qty(row_values[pos + 2])
                material = row_values[pos + 3].replace("[", "").replace("]", "")

                if not part_no or part_no in ["---", "-----"]:
                    continue

                entry = {
                    "option_code": row_values[pos],
                    "part_no": part_no,
                    "qty": qty,
                    "material": material
                }

                if idx == 0:
                    result["ball_options"].append(entry)
                elif idx == 1 and secondary_name:
                    result["secondary_options"].append(entry)

            except IndexError:
                continue

    # Rename secondary section properly
    if secondary_name:
        result[secondary_name] = result.pop("secondary_options")
    else:
        result.pop("secondary_options")

    return result


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def extract_ball_options(pdf_path, page_number):

    df = extract_table_from_pdf(pdf_path, page_number)

    if df is None:
        return {"error": "No BALL option table found on this page"}

    return parse_ball_table(df)


# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------

if __name__ == "__main__":

    PDF_FILE = "PX03P.pdf"   # change file
    PAGE_NUMBER = 5          # change page

    result = extract_ball_options(PDF_FILE, PAGE_NUMBER)

    print(json.dumps(result, indent=2))
