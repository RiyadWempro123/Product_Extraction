import pdfplumber
import pandas as pd
from pathlib import Path
import re
import json

import common_parts_new, common_parts_new_22

# ==========================================================
# CLEANING UTILITIES
# ==========================================================
def table_contains(df, keywords):
    table_text = " ".join(
        str(x) for row in df.values for x in row if pd.notna(x)
    ).upper()
    
    return all(keyword.upper() in table_text for keyword in keywords)


def parse_all_tables(dfs):

    final_json = {}

    for df in dfs:

        full_text = " ".join(
            str(cell) for row in df.values for cell in row if str(cell) != "nan"
        ).upper()
        if "COMMON PARTS" in df:
            common_parts = common_parts_new.common_parts_to_json(df)
            final_json["common_parts"]=common_parts
            
        elif table_contains(df, ["MANIFOLD", "FLUID CAP"]):
            print ("df1111111111111111222222222222", df)
        elif table_contains(df, ["DIAPHRAGM"]):
            print("DIAPHRAGM Options")
            print("df33333", df)
        elif table_contains(df, ["BALL"]):
            print("df444..", df)
        

   
        


        # --------------------------------------------------
        # 5️⃣ DIAPHRAGM OPTIONS
        # --------------------------------------------------
        elif "DIAPHRAGM OPTIONS" in full_text:

            diaphragm_options = []

            for _, row in df.iterrows():
                row_vals = [clean_cell(v) for v in row]

                for i, val in enumerate(row_vals):
                    if val.startswith("-XX"):

                        diaphragm_options.append({
                            "option_code": val,
                            "service_kit": row_vals[i+1],
                            "diaphragm_part": row_vals[i+2],
                            "qty": parse_qty(row_vals[i+3])
                        })

            final_json["diaphragm_options"] = diaphragm_options


        # --------------------------------------------------
        # 6️⃣ DUAL INLET / OUTLET
        # --------------------------------------------------
        elif "DUAL INLET" in full_text:

            dual_kits = []

            for _, row in df.iterrows():
                row_vals = [clean_cell(v) for v in row]

                if row_vals and row_vals[0].isdigit():

                    dual_kits.append({
                        "item": row_vals[0],
                        "description": row_vals[1],
                        "qty": parse_qty(row_vals[2]),
                        "part_no": row_vals[3]
                    })

            final_json["dual_kits"] = dual_kits

    return final_json

def clean_text(text):
    text = str(text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)  # remove non-ascii
    return text.strip()


def clean_cell(cell):
    if cell is None:
        return ""
    return str(cell).replace("\n", " ").strip()


def parse_qty(val):
    if val is None:
        return 0
    val = re.sub(r"[^\d]", "", str(val))
    return int(val) if val else 0


# ==========================================================
# KEYWORDS
# ==========================================================

SEAT_KEYWORDS = {"seat"}
BALL_KEYWORDS = {"ball", "duckbill", "flex"}


# ==========================================================
# DETECT TABLE TYPE
# ==========================================================

def detect_table_type(df):
    """
    Returns: SEAT, BALL, or OTHER
    """

    header_text = " ".join(str(col).lower() for col in df.columns)

    if any(k in header_text for k in SEAT_KEYWORDS):
        return "SEAT"

    if any(k in header_text for k in BALL_KEYWORDS):
        return "BALL"

    return "OTHER"


# ==========================================================
# FIND SPLIT COLUMN (Seat + Ball in same table)
# ==========================================================

def find_split_column(df):
    for idx, col in enumerate(df.columns):
        col_text = str(col).lower()
        if any(k in col_text for k in BALL_KEYWORDS):
            return idx
    return None


# ==========================================================
# SPLIT SEAT & BALL TABLE
# ==========================================================

def split_seat_ball_table(df):

    split_idx = find_split_column(df)

    if split_idx is None:
        return [df]

    seat_df = df.iloc[:, :split_idx].copy()
    ball_df = df.iloc[:, split_idx:].copy()

    seat_df = seat_df.loc[:, seat_df.columns.notna()]
    ball_df = ball_df.loc[:, ball_df.columns.notna()]

    return [seat_df, ball_df]


# ==========================================================
# EXTRACT TABLES + SMART MERGE
# ==========================================================

def extract_tables_as_dataframes(pdf_path, page_number):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extracted_dfs = []

    with pdfplumber.open(pdf_path) as pdf:

        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError("Invalid page number")

        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

        if not tables:
            return extracted_dfs

        raw_dfs = []

        # Convert raw tables to DataFrames
        for table in tables:
            cleaned = [[clean_cell(c) for c in row] for row in table]
            df = pd.DataFrame(cleaned)

            if df.shape[0] > 1:
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)

            raw_dfs.append(df)
        # print("raw_df", raw_dfs)

        # --------------------------------------------------
        # SMART MERGE LOGIC
        # --------------------------------------------------

        i = 0
        while i < len(raw_dfs):

            current_df = raw_dfs[i]

            # If Seat + Ball combined in same table → split
            header_text = " ".join(str(c).lower() for c in current_df.columns)

            if "seat" in header_text and any(k in header_text for k in BALL_KEYWORDS):
                split_tables = split_seat_ball_table(current_df)
                extracted_dfs.extend(split_tables)
                i += 1
                continue

            # Merge side-by-side tables if same row count
            if i + 1 < len(raw_dfs):

                next_df = raw_dfs[i + 1]

                if len(current_df) == len(next_df):
                    merged_df = pd.concat([current_df, next_df], axis=1)
                    extracted_dfs.append(merged_df)
                    i += 2
                    continue

            extracted_dfs.append(current_df)
            i += 1

    # print ("extracted_dfs.................", extracted_dfs)
    return extracted_dfs


# ==========================================================
# PARSE BALL / DUCKBILL OPTIONS
# ==========================================================

def parse_ball_table(df):

    results = []

    for _, row in df.iterrows():

        row_values = [clean_cell(v) for v in row]

        for i, val in enumerate(row_values):

            if isinstance(val, str) and val.startswith("-"):

                entry = {
                    "option_code": val,
                    "part_no": row_values[i + 1] if i + 1 < len(row_values) else "",
                    "qty": parse_qty(row_values[i + 2]) if i + 2 < len(row_values) else 0,
                    "material": row_values[i + 3].replace("[", "").replace("]", "") if i + 3 < len(row_values) else ""
                }

                results.append(entry)

    return results


# ==========================================================
# MAIN PROCESSOR
# ==========================================================

def process_page(pdf_path, page_number):

    all_tables = extract_tables_as_dataframes(pdf_path, page_number)
    json_output = parse_all_tables(all_tables)

    print(json.dumps(json_output, indent=2))
    # for i, df in enumerate(all_tables, start=1):
    #     print(f"----- Table {i} -----")
    #     print(df)
    #     print()
    # final_output = {}

    # for df in all_tables:

    #     table_type = detect_table_type(df)

    #     # Skip Seat tables completely
    #     if table_type == "SEAT":
    #         continue

    #     # Handle Ball / Duckbill / Flex Check
    #     if table_type == "BALL":

    #         ball_entries = parse_ball_table(df)

    #         if ball_entries:
    #             final_output.setdefault("ball_options", []).extend(ball_entries)

    # return final_output


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    PDF_FILE = "PX03P.pdf"
    PAGE_NUMBER = 5

    data = process_page(PDF_FILE, PAGE_NUMBER)

    print(json.dumps(data, indent=2))
