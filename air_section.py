import pdfplumber
import json
import re

PDF_FILE = "manual.pdf"
PAGE_NUMBER = 7
OUTPUT_JSON = "air_section_parts.json"


# ---------------------------------------------------
# CLEAN CELL
# ---------------------------------------------------
def clean(cell):
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()


# ---------------------------------------------------
# NORMALIZE TABLE
# ---------------------------------------------------
def table_to_records(table):
    records = []

    current_left_item = None
    current_right_item = None

    for row in table[2:]:  # skip title + header
        row = [clean(c) for c in row]

        # -------- LEFT SIDE --------
        if row[0]:
            current_left_item = row[0]

        # Only include row if qty exists
        if row[3].strip("()"):
            records.append({
                "item": current_left_item,  # may be None
                "description": row[1],
                "part_no": row[2],
                "qty": row[3].strip("()"),
                "material": row[4].strip("[]")
            })

        # -------- RIGHT SIDE --------
        if row[5]:
            current_right_item = row[5]

        if row[8].strip("()"):
            records.append({
                "item": current_right_item,  # may be None
                "description": row[6],
                "part_no": row[7],
                "qty": row[8].strip("()"),
                "material": row[9].strip("[]")
            })

    return records


# ---------------------------------------------------
# EXTRACT TABLE FROM PDF
# ---------------------------------------------------
def extract_from_pdf(pdf_file, page_number):
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

    all_records = []
    for table in tables:
        all_records.extend(table_to_records(table))

    return all_records


# ---------------------------------------------------
# RUN
# ---------------------------------------------------
if __name__ == "__main__":
    data = extract_from_pdf(PDF_FILE, PAGE_NUMBER)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Extracted {len(data)} records")
    print(f"📄 Saved to {OUTPUT_JSON}")
