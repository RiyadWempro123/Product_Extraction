import pdfplumber
import pandas as pd
import sqlite3
import json
import re
from pathlib import Path


# ==========================================================
# UTILITIES
# ==========================================================




def clean(val):
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


def parse_qty(val):
    if pd.isna(val):
        return 0
    val = re.sub(r"[^\d]", "", str(val))
    return int(val) if val else 0


def extract_option_entries(df, stop_words=None):
    """
    Generic dynamic option extractor.
    Detects -XXX patterns and extracts next columns dynamically.
    Stops if stop_words found in row.
    """

    results = []

    for _, row in df.iterrows():

        row_text = " ".join(row.astype(str)).upper()

        if stop_words:
            if any(word in row_text for word in stop_words):
                break

        row_values = [clean(v) for v in row]

        for i, val in enumerate(row_values):

            if isinstance(val, str) and val.startswith("-"):

                entry = {
                    "option_code": val
                }

                # Try safe extraction dynamically
                try:
                    if i + 1 < len(row_values):
                        entry["part_no"] = row_values[i + 1]

                    if i + 2 < len(row_values):
                        entry["qty"] = parse_qty(row_values[i + 2])

                    if i + 3 < len(row_values):
                        entry["material"] = row_values[i + 3].replace("[","").replace("]","")

                except:
                    pass

                results.append(entry)

    return results


# ==========================================================
# TABLE CLASSIFIER (SMART & FLEXIBLE)
# ==========================================================

def classify_table(df):

    text = " ".join(
        str(cell) for row in df.values for cell in row if str(cell) != "nan"
    ).upper()

    if "COMMON PARTS" in text:
        return "common_parts"

    if "MANIFOLD" in text:
        return "manifold_options"

    if "DUAL INLET" in text:
        return "dual_kits"

    if "DIAPHRAGM OPTIONS" in text:
        return "diaphragm_options"

    # Ignore Seat Tables
    if "SEAT OPTIONS" in text:
        return "ignore"

    # BALL / FLEX CHECK / DUCKBILL
    if "BALL" in text and "OPTIONS" in text:
        if "FLEX CHECK" in text:
            return "flex_check_options"
        if "DUCKBILL" in text:
            return "duckbill_options"
        return "ball_options"

    return None


# ==========================================================
# TABLE PARSERS
# ==========================================================

def parse_common_parts(df):
    results = []

    for _, row in df.iterrows():
        row_values = [clean(v) for v in row if pd.notna(v)]

        if len(row_values) >= 4 and row_values[0].isdigit():
            results.append({
                "item": row_values[0],
                "description": row_values[1],
                "qty": parse_qty(row_values[2]),
                "part_no": row_values[3]
            })

    return results


def parse_ball_family(df, stop_words=None):
    """
    Handles:
    BALL OPTIONS
    BALL / DUCKBILL OPTIONS
    BALL / FLEX CHECK OPTIONS
    """
    result = {}

    text = " ".join(df.iloc[0].astype(str)).upper()

    if "FLEX CHECK" in text:
        secondary_key = "flex_check_options"
    elif "DUCKBILL" in text:
        secondary_key = "duckbill_options"
    else:
        secondary_key = None

    entries = extract_option_entries(df, stop_words=stop_words)

    if secondary_key:
        # Split left and right side dynamically
        mid = len(entries) // 2
        result["ball_options"] = entries[:mid]
        result[secondary_key] = entries[mid:]
    else:
        result["ball_options"] = entries

    return result


def parse_diaphragm_options(df):
    return extract_option_entries(df)


def parse_manifold_options(df):
    return parse_common_parts(df)


def parse_dual_kits(df):
    return parse_common_parts(df)


# ==========================================================
# EXTRACT TABLES
# ==========================================================

def extract_all_tables(pdf_path, page_number):

    tables_data = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError("Invalid page number")

        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

        if not tables:
            return tables_data

        for table in tables:
            df = pd.DataFrame(table)
            df = df.replace("", pd.NA).dropna(how="all")
            tables_data.append(df)

    return tables_data


# ==========================================================
# MAIN PROCESSOR
# ==========================================================

def process_page(pdf_path, page_number):

    all_tables = extract_all_tables(pdf_path, page_number)
    final_output = {}

    for df in all_tables:

        table_type = classify_table(df)

        if table_type is None:
            continue

        if table_type == "ignore":
            continue

        if table_type == "common_parts":
            final_output["common_parts"] = parse_common_parts(df)

        elif table_type in ["ball_options", "flex_check_options", "duckbill_options"]:
            ball_data = parse_ball_family(df, stop_words=["SEAT OPTIONS"])
            final_output.update(ball_data)

        elif table_type == "diaphragm_options":
            final_output["diaphragm_options"] = parse_diaphragm_options(df)

        elif table_type == "manifold_options":
            final_output["manifold_options"] = parse_manifold_options(df)

        elif table_type == "dual_kits":
            final_output["dual_kits"] = parse_dual_kits(df)

    return final_output


# ==========================================================
# DATABASE STORAGE
# ==========================================================

def save_ball_options_to_db(data):

    conn = sqlite3.connect("parts.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ball_options (
            option_code TEXT,
            part_no TEXT,
            qty INTEGER,
            material TEXT
        )
    """)

    ball_data = data.get("ball_options", [])

    for item in ball_data:
        cursor.execute("""
            INSERT INTO ball_options VALUES (?, ?, ?, ?)
        """, (
            item.get("option_code"),
            item.get("part_no"),
            item.get("qty", 0),
            item.get("material", "")
        ))

    conn.commit()
    conn.close()


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    PDF_FILE = "PX03P.pdf"
    PAGE_NUMBER = 5

    data = process_page(PDF_FILE, PAGE_NUMBER)

    print(json.dumps(data, indent=2))

    save_ball_options_to_db(data)
