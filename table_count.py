import pdfplumber
import pandas as pd
from pathlib import Path

import re

def clean_text(text):
    text = str(text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)  # remove non-ascii
    return text.strip()

# --------------------------------------------------
# KEYWORDS
# --------------------------------------------------
SEAT_KEYWORDS = {"seat"}
BALL_KEYWORDS = {"ball", "duckbill"}

# --------------------------------------------------
# CLEAN CELL TEXT
# --------------------------------------------------
def clean_cell(cell):
    if cell is None:
        return ""
    return str(cell).replace("\n", " ").strip()

# --------------------------------------------------                                            
# DETECT TABLE TYPE
# --------------------------------------------------
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

# --------------------------------------------------
# FIND SPLIT COLUMN
# --------------------------------------------------
def find_split_column(df):
    """
    Finds column index where Ball/Duckbill section starts
    """
    for idx, col in enumerate(df.columns):
        col_text = str(col).lower()
        if any(k in col_text for k in BALL_KEYWORDS):
            return idx
    return None

# --------------------------------------------------
# SPLIT SEAT & BALL TABLE
# --------------------------------------------------
def split_seat_ball_table(df):
    split_idx = find_split_column(df)
    if split_idx is None:
        return [df]

    seat_df = df.iloc[:, :split_idx].copy()
    ball_df = df.iloc[:, split_idx:].copy()

    # Drop empty columns
    seat_df = seat_df.loc[:, seat_df.columns.notna()]
    ball_df = ball_df.loc[:, ball_df.columns.notna()]

    return [seat_df, ball_df]

# --------------------------------------------------
# EXTRACT TABLES AND MERGE SIDE-BY-SIDE TABLES
# --------------------------------------------------
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

        # Convert raw tables to DataFrames
        raw_dfs = []
        for table in tables:
            cleaned = [[clean_cell(c) for c in row] for row in table]
            df = pd.DataFrame(cleaned)

            if df.shape[0] > 1:
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)

            raw_dfs.append(df)

        # --------------------------------------------------
        # MERGE TABLES THAT ARE ON THE SAME ROW (SMART)
        # --------------------------------------------------
        i = 0
        while i < len(raw_dfs):
            current_df = raw_dfs[i]
            current_type = detect_table_type(current_df)

            # -------- Split Seat & Ball in same table --------
            header_text = " ".join(str(c).lower() for c in current_df.columns)
            if "seat" in header_text and ("ball" in header_text or "duckbill" in header_text):
                split_tables = split_seat_ball_table(current_df)
                extracted_dfs.extend(split_tables)
                i += 1
                continue

            # -------- Merge side-by-side tables --------
            if i + 1 < len(raw_dfs):
                next_df = raw_dfs[i + 1]
                next_type = detect_table_type(next_df)

                # Same row layout (same number of rows)
                if len(current_df) == len(next_df):
                    # Do not merge Seat & Ball (already handled above)
                    merged_df = pd.concat([current_df, next_df], axis=1)
                    extracted_dfs.append(merged_df)
                    i += 2
                    continue

            # Default: append as-is
            extracted_dfs.append(current_df)
            i += 1

    return extracted_dfs



# --------------------------------------------------
# EXAMPLE USAGE
# --------------------------------------------------
if __name__ == "__main__":
    PDF_FILE = "PX03P.pdf"
    PAGE_NUMBER = 5

    dfs = extract_tables_as_dataframes(PDF_FILE, PAGE_NUMBER)

    print(f"Total logical tables found: {len(dfs)}\n")

    for i, df in enumerate(dfs, start=1):
        print(f"----- Table {i} -----")
        print(df)
        print()
       
