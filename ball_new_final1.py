import pdfplumber
import json
import re

PDF_FILE = "661PX.pdf"
PAGE_NUMBER = 5
OUTPUT_JSON = "ball_options.json"

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
# Check if table is Ball Options
# ----------------------------
def is_ball_options_table(table):
    # Scan all cells in the first few rows for "BALL" but ignore "SEAT OPTIONS"
    for row in table[:2]:
        for cell in row:
            if cell:
                text = clean_text(cell)
                if re.search(r"(BALL|FLEX CHECK)", text, re.IGNORECASE) and "SEAT OPTIONS" not in text.upper():
                    return True
    return False

# ----------------------------
# Parse Ball Options table (handles multiple portions per row)
# ----------------------------
def parse_ball_table(table):
    records = []

    # Detect where BALL OPTIONS starts
    first_row_texts = [clean_text(c) for c in table[0]]

    ball_start_index = None
    for i, cell in enumerate(first_row_texts):
        if cell:
            cell_clean = clean_text(cell)
            if re.search(r"(BALL|FLEX CHECK)", cell_clean, re.IGNORECASE) and "SEAT OPTIONS" not in cell_clean.upper():
                ball_start_index = i
                break

    if ball_start_index is None:
        return []

    # Find header row (contains "Ball")
    header_row_index = None
    for idx, row in enumerate(table):
        row_clean = [clean_text(c) for c in row]
        if any("BALL" in c.upper() for c in row_clean):
            header_row_index = idx
            break

    if header_row_index is None:
        return []

    # Data rows
    for row in table[header_row_index + 1:]:
        row = [clean_text(c) if c else "" for c in row]

        i = ball_start_index

        while i < len(row):

            # Skip empty separator columns
            if not row[i]:
                i += 1
                continue

            chunk = row[i:i+4]

            if len(chunk) < 4:
                break

            code, part_number, qty_raw, material_raw = chunk

            # Validate code
            if not code.startswith("-"):
                i += 1
                continue

            # Extract quantity
            qty_match = re.search(r'(\d+)', qty_raw)
            if not qty_match:
                i += 1
                continue

            qty = int(qty_match.group(1))

            # Extract material
            material_match = re.search(r'\[?(\w+)\]?', material_raw)
            material = material_match.group(1) if material_match else None

            records.append({
                "code": code,
                "part_number": part_number,
                "qty": qty,
                "material": material
            })

            # Move to next block
            i += 4

    return records

# ----------------------------
# Extract Ball Options from PDF
# ----------------------------
def extract_ball_options_from_pdf(pdf_file, page_number):
    all_records = []

    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables()
        if not tables:
            return []

        for table in tables:
            if is_ball_options_table(table):
                ball_records = parse_ball_table(table)
                all_records.extend(ball_records)

    return all_records

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    data = extract_ball_options_from_pdf(PDF_FILE, PAGE_NUMBER)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Extracted {len(data)} Ball Option records")
    print(f"📄 Saved to {OUTPUT_JSON}")