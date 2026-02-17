import pdfplumber
import pandas as pd
import re

PDF_PATH = "manual_.pdf"
OUTPUT_CSV = "common_parts.csv"

# ----------------------------------------
# 1) Read left column text
# ----------------------------------------
all_lines = []

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        words = page.extract_words(use_text_flow=True)
        left_words = [w for w in words if w["x0"] < page.width * 0.55]

        lines_by_top = {}
        for w in left_words:
            key = round(w["top"])
            lines_by_top.setdefault(key, []).append(w)

        for top in sorted(lines_by_top):
            line = " ".join(
                w["text"] for w in sorted(lines_by_top[top], key=lambda x: x["x0"])
            )
            all_lines.append(line.strip())

# ----------------------------------------
# 2) Extract COMMON PARTS block
# ----------------------------------------
common_lines = []
inside = False

for line in all_lines:
    U = line.upper()
    if "COMMON PARTS" in U:
        inside = True
        continue
    if inside and ("FLUID CONNECTION" in U or "CENTER BODY" in U):
        break
    if inside:
        common_lines.append(line)

# ----------------------------------------
# 3) Remove material code legend
# ----------------------------------------
filtered = []
for l in common_lines:
    if re.match(r"\[[A-Za-z]+\]\s*=", l):
        continue
    if "MATERIAL CODE" in l.upper():
        continue
    filtered.append(l)

# ----------------------------------------
# 4) Merge multi-line items until last token is numeric (part number)
# ----------------------------------------
rows_raw = []
buf = ""
for line in filtered:
    line = line.strip()
    if re.match(r"^\d+\s", line) and buf and re.search(r"\d+$", buf):
        rows_raw.append(buf.strip())
        buf = line
    else:
        buf += " " + line
if buf:
    rows_raw.append(buf.strip())

# ----------------------------------------
# 5) Parse rows robustly
# ----------------------------------------
KNOWN_MATERIALS = ["P", "SS", "T", "U", "V", "GP"]

data = []

for r in rows_raw:
    r = r.strip()

    # Item number
    item_match = re.match(r"^(\d+)", r)
    if not item_match:
        continue
    item = item_match.group(1)

    # Part number: last numeric token (could be 23981541 or 93616-1)
    part_match = re.findall(r"(\d{1,6}-?\d*)$", r)
    part_no = part_match[-1] if part_match else ""

    # Quantity: last bracketed number BEFORE part_no
    qty_match = re.findall(r"\[(\d+)\]", r)
    qty = qty_match[-1] if qty_match else "1"

    # Material code: first bracketed token from known list
    mat_match = re.findall(r"\[([A-Za-z]+)\]", r)
    material = ""
    for m in mat_match:
        if m in KNOWN_MATERIALS:
            material = m
            break

    # Description cleanup
    desc = r
    desc = re.sub(r"^\d+\s*", "", desc)  # remove item
    desc = re.sub(rf"\[{qty}\]", "", desc)  # remove quantity
    if material:
        desc = re.sub(rf"\[{material}\]", "", desc)
    desc = desc.replace(part_no, "")
    desc = re.sub(r"\[.*?\]", "", desc)  # remove leftover brackets
    desc = re.sub(r"\s{2,}", " ", desc).strip()

    data.append({
        "Item": item,
        "Description": desc,
        "Material": material,
        "Quantity": qty,
        "Part Number": part_no
    })

# ----------------------------------------
# 6) Save CSV
# ----------------------------------------
df = pd.DataFrame(data)
df.to_csv(OUTPUT_CSV, index=False)
print("\n====== FINAL COMMON PARTS ======")
print(df)
print("\nSaved to:", OUTPUT_CSV)
