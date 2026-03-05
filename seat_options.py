import pdfplumber
import json
import re

PDF_FILE = "PX03P.pdf"
PAGE_NUMBER = 5
OUTPUT_JSON = "seat_options.json"

# ----------------------------
# Clean text
# ----------------------------
def clean_text(text):
    if text is None:
        return ""
    text = str(text).replace("\n", " ").strip()
    text = re.sub(r'[\uf000-\uf0ff]', '', text)  # remove PDF special chars
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r'\s+', ' ', text)  # normalize spaces
    return text.strip()


def parse_seat_table(table):
    records = []

    # Validate this is SEAT OPTIONS table
    first_row_text = clean_text(table[0][0])
    if "SEAT OPTIONS" not in first_row_text.upper():
        return []

    # Start from row 3 (actual data rows)
    for row in table[3:]:
        row = [clean_text(c) for c in row]

        # Process row in chunks of 4 columns
        for i in range(0, len(row), 4):
            chunk = row[i:i+4]

            if len(chunk) < 4:
                continue

            code, part_number, qty_raw, material_raw = chunk

            # Skip empty blocks
            if not code or not part_number:
                continue

            # Validate structure
            if (
                code.startswith("-") and
                qty_raw.startswith("(") and
                material_raw.startswith("[")
            ):
                qty = int(re.sub(r"[^\d]", "", qty_raw))
                material = re.sub(r"[\[\]]", "", material_raw)

                records.append({
                    "code": code,
                    "part_number": part_number,
                    "qty": qty,
                    "material": material
                })

    return records



def parse_seat_table1(table):
    records = []

    # Check this is really SEAT OPTIONS table
    first_row_text = clean_text(table[0][0])
    if "SEAT OPTIONS" not in first_row_text.upper():
        return []

    # Start from row index 3 (actual data row)
    for row in table[3:]:
        row = [clean_text(c) for c in row]

        # Ensure row has expected 4 columns
        if len(row) < 4:
            continue

        code = row[0]
        part_number = row[1]
        qty_raw = row[2]
        material_raw = row[3]

        # Validate format
        if (
            code.startswith("-") and
            part_number and
            qty_raw.startswith("(") and
            material_raw.startswith("[")
        ):
            qty = int(re.sub(r"[^\d]", "", qty_raw))
            material = re.sub(r"[\[\]]", "", material_raw)

            records.append({
                "code": code,
                "part_number": part_number,
                "qty": qty,
                "material": material
            })

    return records

# ----------------------------
# Extract Seat Options from a table
# ----------------------------
def parse_seat_table1(table):
    records = []

    # Skip table if header contains "BALL OPTIONS"
    first_row_text = " ".join([clean_text(c) for c in table[0]])
    if "BALL OPTIONS" in first_row_text.upper():
        return []

    for row in table[2:]:  # skip title/header
        row = [clean_text(c) for c in row]

        # Join row into one string for regex
        row_text = " ".join(row)

        # Regex: code, part number, qty, material
        match = re.search(r"(-[A-Z0-9-]+)\s+([\d-]+)\s+\((\d+)\)\s+\[([A-Z]+)\]", row_text)
        if match:
            records.append({
                "code": match.group(1),
                "part_number": match.group(2),
                "qty": int(match.group(3)),
                "material": match.group(4)
            })

    return records

# ----------------------------
# Extract tables from PDF
# ----------------------------
def extract_seat_options_from_pdf(pdf_file, page_number):
    all_records = []

    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()
        # print('tables', tables)
        if not tables:
            return []

        for table in tables:
            print("table........", table )
            seat_records = parse_seat_table(table)
            all_records.extend(seat_records)

    return all_records

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    data = extract_seat_options_from_pdf(PDF_FILE, PAGE_NUMBER)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Extracted {len(data)} seat option records")
    print(f"📄 Saved to {OUTPUT_JSON}")
