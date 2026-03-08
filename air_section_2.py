import pdfplumber
import json
import re

PDF_FILE = "manual2.pdf"
PAGE_NUMBER = 8
OUTPUT_JSON = "air_section_parts.json"



def clean(cell):
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()

def clean_text(value):
    if value is None:
        return ""

    text = str(value)

    # remove pdf special unicode icons
    text = re.sub(r'[\uf000-\uf0ff]', '', text)

    # normalize quotes
    text = text.replace("“", '"').replace("”", '"')

    # keep only letters, numbers, space and few safe symbols
    text = re.sub(r'[^A-Za-z0-9\s\-\(\)\/\.\"]', '', text)

    # normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def clean_text1(value):
    if value is None:
        return ""

    text = str(value)

    # remove pdf special unicode icons
    text = re.sub(r'[\uf000-\uf0ff]', '', text)

    # normalize quotes
    text = text.replace("“", '"').replace("”", '"')

    # keep only letters, numbers, space and few safe symbols
    text = re.sub(r'[^A-Za-z0-9\s\-\(\)\/\.\"]', '', text)

    # normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()



def table_to_records(table):
    records = []

    current_left_item = None
    current_right_item = None

    for row in table[2:]:  
        row = [clean(c) for c in row]
        cols = len(row)

        # ---------------- LEFT TABLE ----------------
        if cols >= 5:

            # keep previous item if empty
            if row[0]:
                current_left_item = clean_text(row[0])

            if row[3].strip("()"):

                part_no = ""
                qty = ""

                data1 = clean_text(row[2])
                data2 = clean_text(row[3])

                if len(data1) <= 3:
                    qty = data1.strip("()")
                else:
                    part_no = data1

                if len(data2) <= 3:
                    qty = data2.strip("()")
                else:
                    part_no = data2

                records.append({
                    "item": current_left_item,
                    "description": clean_text(row[1]),
                    "part_no": part_no,
                    "qty": qty,
                    "material": row[4].strip("[]")
                })

        # ---------------- RIGHT TABLE ----------------
        if cols >= 10:

            if row[5]:
                current_right_item = clean_text(row[5])

            if row[8].strip("()"):

                part_no = ""
                qty = ""

                data3 = clean_text(row[7])
                data4 = clean_text(row[8])

                if len(data3) <= 3:
                    qty = data3.strip("()")
                else:
                    part_no = data3

                if len(data4) <= 3:
                    qty = data4.strip("()")
                else:
                    part_no = data4

                records.append({
                    "item": current_right_item,
                    "description": clean_text(row[6]),
                    "part_no": part_no,
                    "qty": qty,
                    "material": row[9].strip("[]")
                })

    return records


def extract_from_pdf(pdf_file, page_number):
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()
        if not tables:
            print("No tables found on this page.")
            return []

    all_records = []
    for table in tables:
        all_records.extend(table_to_records(table))

    return all_records


if __name__ == "__main__":
    data = extract_from_pdf(PDF_FILE, PAGE_NUMBER)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f" Extracted {len(data)} records")
    print(f" Saved to {OUTPUT_JSON}")