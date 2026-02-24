import pdfplumber
import pandas as pd
import json
import re
from pathlib import Path


# --------------------------------------------------
# CLEAN CELL
# --------------------------------------------------
def clean(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


# --------------------------------------------------
# VALIDATION HELPERS
# --------------------------------------------------
def is_valid(value):
    """Return True if a value is a real part number/qty/material."""
    if value is None:
        return False

    value = str(value).strip()

    # List of invalid/placeholder values
    invalid_values = [
        "", "-", "--", "---", "-----", "- - -", "- - - - -",
        ""
        "\uf0ab “7”", "\uf0ab “8”", "\uf0ab “19”", "\uf0ab “33”",
        "<NA>"
    ]

    return value not in invalid_values

def safe_int(value):

    if value is None:
        return None

    value = str(value).replace("(", "").replace(")", "").strip()

    if not value.isdigit():
        return None

    return int(value)


def clean_material(val):

    if val is None:
        return None
    

    return re.sub(r"[\[\]]", "", str(val)).strip()


def safe_get(row, index):

    if index >= len(row):
        return None

    return row.iloc[index]


# --------------------------------------------------
# FIND DIAPHRAGM TABLE
# --------------------------------------------------
def extract_diaphragm_table(pdf_path):

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                flat_text = " ".join(
                    clean(c) for row in table for c in row if clean(c)
                ).upper()

                if "DIAPHRAGM OPTIONS" in flat_text:

                    df = pd.DataFrame([[clean(c) for c in row] for row in table])

                    df = df.replace("", pd.NA).dropna(how="all").reset_index(drop=True)

                    return df

    return None


# --------------------------------------------------
# PARSE DIAPHRAGM OPTIONS
# --------------------------------------------------
def parse_diaphragm_df(df):

    results = []

    for _, row in df.iterrows():

        option_code = str(safe_get(row, 0)).strip()

        # --------------------------------------------------
        # Skip invalid rows
        # --------------------------------------------------

        if not re.match(r"^-XX[A-Z]$", option_code):
            continue

        service_with = safe_get(row, 1)
        service_without = safe_get(row, 2)
        if option_code=="-XXX":
            continue
        entry = {
            "option_code": option_code,
            "service_kits": {
                "with_seat": service_with,
                "without_seat": service_without
            },
            "components": {}
        }

        # --------------------------------------------------
        # DIAPHRAGM 7
        # --------------------------------------------------

        part = safe_get(row, 3)

        if is_valid(part):

            entry["components"]["diaphragm_7"] = {
                "part_no": part,
                "qty": safe_int(safe_get(row, 4)),
                "material": clean_material(safe_get(row, 5))
            }

        # --------------------------------------------------
        # DIAPHRAGM 8
        # --------------------------------------------------

        part = safe_get(row, 6)

        if is_valid(part):

            entry["components"]["diaphragm_8"] = {
                "part_no": part,
                "qty": safe_int(safe_get(row, 7)),
                "material": clean_material(safe_get(row, 8))
            }

        # --------------------------------------------------
        # O-RING 19
        # --------------------------------------------------

        part = safe_get(row, 9)

        if is_valid(part):
            entry["components"]["diaphragm_19"] = {
                "part_no": part,
                "qty": safe_int(safe_get(row, 10)),
                "material": clean_material(safe_get(row, 11))
            }

        # --------------------------------------------------
        # O-RING 33
        # --------------------------------------------------

        part = safe_get(row, 12)

        if is_valid(part):
            
            entry["components"]["diaphragm_33"] = {
                "part_no": part,
                "qty": safe_int(safe_get(row, 13)),
                "material": clean_material(safe_get(row, 14))
            }

        results.append(entry)

    return results


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def extract_px20_diaphragm(pdf_path):

    df = extract_diaphragm_table(pdf_path)

    if df is None:
        return {}

    return {
        "table_name": "DIAPHRAGM OPTIONS",
        "model": "PX20X-XXX-XXX-AXXX",
        "options": parse_diaphragm_df(df)
    }


# --------------------------------------------------
# RUN SCRIPT
# --------------------------------------------------
if __name__ == "__main__":

    PDF_FILE = "PX20X.pdf"

    result = extract_px20_diaphragm(PDF_FILE)

    print(json.dumps(result, indent=2))
