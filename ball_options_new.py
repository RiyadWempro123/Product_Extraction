import pdfplumber
import json
import re

PDF_FILE = "PX20P.pdf"
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
# Parse Ball Options table (supports two parts)
# ----------------------------
def parse_ball_table(table):
    records = []

    # Combine first row to detect header positions
    first_row_texts = [clean_text(c) for c in table[0]]
   

    # Find the column index where BALL / FLEX CHECK starts
    ball_start_index = 0
    for i, cell in enumerate(first_row_texts):
        print("cell..", cell )
        if cell and re.search(r"(BALL|FLEX CHECK)", cell, re.IGNORECASE):
            ball_start_index = i
            break

    for row in table[1:]:  # skip header row
        row = [clean_text(c) if c else "" for c in row]

        # Split row into left and right parts if table is two-part
        left_part = row[ball_start_index:ball_start_index + 5]  # adjust 5 if more columns per part
        right_part = row[ball_start_index + 5:]  # remaining columns

        # Function to parse a row slice
        def parse_columns(cols):
            row_text = " ".join(cols)
            match = re.search(r"(-[A-Z0-9-]+)\s+([\d-]+(?:-[A-Z])?)\s*\(?(\d+)\)?\s*(?:\[(\w+)\])?", row_text)
            if match:
                return {
                    "code": match.group(1),
                    "part_number": match.group(2),
                    "qty": int(match.group(3)),
                    "material": match.group(4) if match.group(4) else None
                }
            return None

        left_record = parse_columns(left_part)
        right_record = parse_columns(right_part)

        if left_record:
            records.append(left_record)
        if right_record:
            records.append(right_record)

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
