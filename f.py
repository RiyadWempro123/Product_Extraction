import pdfplumber
import pandas as pd
import re

PDF_PATH = "manual.pdf"

# 1️⃣ Extract all lines
lines = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        t = page.extract_text()
        if t:
            lines.extend([l.strip() for l in t.split("\n") if l.strip()])

# 2️⃣ Extract COMMON PARTS section
common_lines = []
inside_common = False
for line in lines:
    if "COMMON PARTS" in line.upper():
        inside_common = True
        continue
    # Stop at first material note like [B] = Nitrile
    if inside_common and re.match(r"\[[A-Z]\]", line):
        break
    if inside_common:
        common_lines.append(line)

if not common_lines:
    print("No lines found in COMMON PARTS. Check PDF text extraction.")
else:
    print(f"Found {len(common_lines)} lines in COMMON PARTS")

# 3️⃣ Merge multi-line items
merged_lines = []
buffer = ""
for line in common_lines:
    # Start of new item: line begins with digit
    if re.match(r"^\d+", line):
        if buffer:
            merged_lines.append(buffer.strip())
        buffer = line
    else:
        buffer += " " + line
if buffer:
    merged_lines.append(buffer.strip())

# Print to debug
print("---- Merged Lines ----")
for l in merged_lines:
    print(l)

# 4️⃣ Parse items into structured table
rows = []
for line in merged_lines:
    # Item number
    item_match = re.match(r"^(\d+)", line)
    if not item_match:
        continue
    item = item_match.group(1)

    # Quantity in brackets
    qty_match = re.search(r"\[?(\d+)\]?", line)
    qty = qty_match.group(1) if qty_match else "1"

    # Part number at end
    part_match = re.search(r"([A-Za-z0-9\-]+)$", line)
    part = part_match.group(1) if part_match else ""

    # Description
    desc = line
    desc = re.sub(rf"^{item}", "", desc)
    desc = re.sub(rf"\[{qty}\]", "", desc)
    desc = re.sub(rf"{part}$", "", desc)
    desc = desc.replace("---", "").strip()

    rows.append({
        "Item": item.strip(),
        "Description": desc.strip(),
        "Quantity": qty.strip(),
        "Part Number": part.strip()
    })

# 5️⃣ Convert to DataFrame
if rows:
    df = pd.DataFrame(rows)
    # Remove empty descriptions
    df = df[df["Description"].str.len() > 0]
    print(df)
else:
    print("No items found after parsing. Check PDF text extraction.")
