import pdfplumber
import pandas as pd
import json
from pathlib import Path

# ------------------------
# CLEAN CELL
# ------------------------
def clean_cell(cell):
    if cell is None:
        return ""
    return str(cell).replace("\n", " ").strip()

# ------------------------
# CONVERT DATAFRAME TO JSON
# ------------------------
def dataframe_to_json(df):
    """
    Converts a pandas DataFrame to JSON (list of dicts)
    """
    df = df.fillna("")  # Replace NaN with empty string
    return df.to_dict(orient="records")

# ------------------------
# EXTRACT TABLES AND CLEAN
# ------------------------
def extract_tables_as_json(pdf_path, page_number):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    all_tables_json = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError("Invalid page number")

        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

        if not tables:
            return all_tables_json

        for table in tables:
            # Clean table cells
            cleaned = [[clean_cell(c) for c in row] for row in table]

            df = pd.DataFrame(cleaned)

            # Treat first row as header if possible
            if df.shape[0] > 1:
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)

            # Convert to JSON
            table_json = dataframe_to_json(df)
            all_tables_json.append(table_json)

    return all_tables_json

# ------------------------
# EXAMPLE USAGE
# ------------------------
if __name__ == "__main__":
    PDF_FILE = "PX03P.pdf"
    PAGE_NUMBER = 5

    tables_json = extract_tables_as_json(PDF_FILE, PAGE_NUMBER)

    # Print JSON nicely
    for i, table in enumerate(tables_json, start=1):
        print(f"----- Table {i} JSON -----")
        print(json.dumps(table, indent=2, ensure_ascii=False))
        print()
