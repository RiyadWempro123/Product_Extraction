import pdfplumber
import json
import re

PDF_FILE = "manual2.pdf"
PAGE_NUMBER = 6
OUTPUT_JSON = "air_section_common_parts.json"

# ---------------- CLEAN FUNCTIONS ----------------
def clean(cell):
    if cell is None:
        return ""
    # Keep only printable characters
    cell = ''.join(c for c in str(cell) if c.isprintable())
    return re.sub(r"\s+", " ", cell).strip()

def clean_text(value):
    if value is None:
        return ""

    text = str(value)

    # Remove private unicode glyphs
    text = re.sub(r'[\uf000-\uf0ff]', '', text)

    # Replace smart quotes with normal ones
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00d8", "")

    # Remove duplicate quotes at beginning
    text = re.sub(r'^["\']+', '', text)

    # Remove trailing special characters like #, *, etc.
    text = re.sub(r'[\s#*]+$', '', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# ---------------- PART + QTY + MATERIAL EXTRACTION ----------------
def extract_part_qty(val1, val2, val3):
    part_no = ""
    qty = ""
    mtl = ""

    for val in [val1, val2, val3]:
        raw_val = str(val)
        text = clean_text(val)

        if not text:
            continue

        # Quantity = only digits (1-3 digits)
        qty_match = re.search(r'^[\[\(]?\s*(\d{1,3})\s*[\]\)]?$', text)
        if qty_match:
            qty = qty_match.group(1)
        
        # Material inside brackets like [SS]
        elif "[" in raw_val and "]" in raw_val:
            mtl_match = re.search(r"\[([A-Za-z]+)\]", raw_val)
            if mtl_match:
                mtl_candidate = mtl_match.group(1)
                if mtl_candidate.isalpha() and 1 <= len(mtl_candidate) <= 5:
                    mtl = mtl_candidate
        
        # Otherwise treat as part number
        else:
            # Remove trailing unwanted chars but keep valid ones like -, _
            part_no = re.sub(r'[^A-Za-z0-9\-_]+$', '', text)

    return part_no, qty, mtl

# ---------------- TABLE ROW PARSER ----------------
def table_to_records(table):
    records = []
    current_left_item = ""
    current_right_item = ""

    for row in table:
        row = [clean(c) for c in row]

        # Skip empty rows
        if not any(row):
            continue

        # Skip header rows
        row_text = " ".join(row).lower()
        if "item" in row_text and "description" in row_text:
            continue

        cols = len(row)

        # ---------------- LEFT SIDE ----------------
        if cols >= 5:
            if row[0]:
                current_left_item = row[0]

            part_no, qty, mtl = extract_part_qty(row[2], row[3], row[4])

            if part_no or qty:
                records.append({
                    "item": clean_text(current_left_item),
                    "description": clean_text(row[1]),
                    "part_no": clean_text(part_no),
                    "qty": clean_text(qty),
                    "material": clean_text(mtl)
                })

        # ---------------- RIGHT SIDE ----------------
        if cols >= 10:
            if row[5]:
                current_right_item = row[5]

            part_no, qty, mtl = extract_part_qty(row[7], row[8], row[9])

            if part_no or qty:
                records.append({
                    "item": clean_text(current_right_item),
                    "description": clean_text(row[6]),
                    "part_no": clean_text(part_no),
                    "qty": clean_text(qty),
                    "material": clean_text(mtl)
                })

    return records

# ---------------- DETECT COMMON PARTS TABLE ----------------
def is_common_parts_table(table, header_name="Common Parts"):
    for i in range(min(2, len(table))):
        row = table[i]
        if row:
            row_text = " ".join([clean_text(c).lower() for c in row if c])
            if header_name.lower() in row_text:
                return True
    return False

# ---------------- EXTRACT ONLY COMMON PARTS ----------------
def extract_common_parts(pdf_file, page_number):
    common_records = []
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()

        for table in tables:
            if is_common_parts_table(table):
                records = table_to_records(table)
                common_records.extend(records)

    return common_records

# ---------------- RUN ----------------
if __name__ == "__main__":
    data = extract_common_parts(PDF_FILE, PAGE_NUMBER)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Extracted {len(data)} common parts")
    print(f"📄 Saved to {OUTPUT_JSON}")