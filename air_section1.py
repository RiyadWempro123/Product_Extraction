import pdfplumber
import json
import re

PDF_FILE = "PX07P.pdf"
PAGE_NUMBER = 8
OUTPUT_JSON = "air_section_parts.json"


# ---------------------------------------------------
# CLEAN CELL
# ---------------------------------------------------
def clean(cell):
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()

import re

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
    # print ("Text", text)

    return text.strip()

# ---------------------------------------------------
# NORMALIZE TABLE
# ---------------------------------------------------
def table_to_records(table):
    records = []

    current_left_item = None
    current_right_item = None

    for row in table[2:]:  # skip title + header
        row = [clean(c) for c in row]
        cols = len(row)
        if cols >= 5:
        # -------- LEFT SIDE --------
            if row[0]:
                current_left_item = row[0]

            # Only include row if qty exists
            part_no = None
            if row[3].strip("()"):
                data1 = clean_text(row[2])
                print ("data1...", data1)
                if len(data1)<=3:
                    qty = str(data1)[1:2]
                    print("qty", qty)
                else:
                    part_no=data1
                    print("part_no", part_no)
                data2 = clean_text(row[3])
                print ("data2...", data2)
                if len(data2)<=3:
                    qty = str(data2)[1:2]
                    print("qty2", qty)
                else:
                    part_no = data2
                    print("part_no2", part_no)
                    
                
                
                records.append({
                    "item": clean_text (current_left_item),  # may be None
                    "description": clean_text(row[1]),
                    "part_no": part_no,
                    "qty": qty,
                    "material": row[4].strip("[]")
                })
                print("records", records)

        # -------- RIGHT SIDE --------
        if cols >= 10:
            if row[5]:
                current_right_item = row[5]

            if row[8].strip("()"):
                
                data3 = clean_text(row[7])
                print ("data right...", data3)
                if len(data3)<=3:
                    qty = str(data1)[1:2]
                    print("qty right", qty)
                else:
                    part_no=data3
                    print("part_no right", part_no)
                data4 = clean_text(row[8])
                print ("data... right", data4)
                if len(data4)<=3:
                    qty = str(data2)[1:2]
                    print("qty right", qty)
                else:
                    part_no = data4
                    print("part_no right", part_no)
                
                
                records.append({
                    "item": clean_text(current_right_item),  # may be None
                    "description": clean_text(row[6]),
                    "part_no": part_no,
                    "qty": qty,
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
        print("tables", tables)
        

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
    print("Data extraction ")
   
    

