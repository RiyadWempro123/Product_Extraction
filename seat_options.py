import pdfplumber
import json
import re

PDF_FILE = "manual.pdf"
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

# ----------------------------
# Extract Seat Options from a table
# ----------------------------
def parse_seat_table(table):
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
        if not tables:
            return []

        for table in tables:
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
