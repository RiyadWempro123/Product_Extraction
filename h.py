# import pdfplumber
# import re
# import json

# PDF = "manual.pdf"
# OUTPUT_JSON = "common_parts.json"

# lines = []

# # 1) Read left column text
# with pdfplumber.open(PDF) as pdf:
#     for page in pdf.pages:
#         words = page.extract_words(use_text_flow=True)
#         left = [w for w in words if w["x0"] < page.width * 0.55]
#         rows = {}
#         for w in left:
#             y = round(w["top"])
#             rows.setdefault(y, []).append(w)
#         for y in sorted(rows):
#             line = " ".join(w["text"] for w in sorted(rows[y], key=lambda x: x["x0"]))
#             lines.append(line.strip())

# # 2) Extract COMMON PARTS block
# common = []
# inside = False
# for l in lines:
#     u = l.upper()
#     if "COMMON PARTS" in u:
#         inside = True
#         continue
#     if inside and ("FLUID CONNECTION" in u or "CENTER BODY" in u):
#         break
#     if inside:
#         common.append(l)

# # 3) Parse items
# items = []
# current_item = None
# pending_part_no = None

# for line in common:
#     # Pure number = pending part number
#     if re.fullmatch(r"\d{4,8}-?\d*", line):
#         pending_part_no = line
#         continue

#     # Item line: starts with number
#     m = re.match(r"^(\d+)(.*)", line)
#     if m:
#         # Save previous item
#         if current_item:
#             items.append(current_item)

#         current_item = {
#             "Item": m.group(1).strip(),
#             "Description": m.group(2).strip().replace("---",""),
#             "Material": "---",
#             "Quantity": "1",
#             "Part Number": pending_part_no if pending_part_no else ""
#         }
#         pending_part_no = None
#         continue

#     if not current_item:
#         continue

#     # Material / Quantity / Part Number line
#     mat = re.search(r"\[([A-Za-z]+)\]", line)
#     quantity = re.findall(r"\[(\d+)\]", line)
#     pn = re.search(r"\b\d{4,8}-?\d*\b", line)
    

#     if mat:
#         current_item["Material"] = mat.group(1)
#     if quantity:
#         # Take last bracket as Quantity
#         current_item["Quantity"] = quantity[-1]
#     if pn:
#         current_item["Part Number"] = pn.group()

#     # Description continuation
#     if line.startswith("("):
#         current_item["Description"] += " " + line
# # Add last item
# if current_item:
#     items.append(current_item)

# # 4) Save JSON
# with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
#     json.dump(items, f, indent=2)

# # Print JSON
# print(json.dumps(items, indent=2))

import pdfplumber
import json



def extract_common_parts(pdf_path, page_number):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        words = page.extract_words(use_text_flow=True)

        rows = {}
        for w in words:
            y = round(w["top"], 1)
            rows.setdefault(y, []).append(w)

        for y in sorted(rows):
            row = rows[y]

            item = ""
            desc = ""
            material = ""
            qty = ""
            part = ""

            for w in row:
                x = w["x0"]
                t = w["text"]

                if 40 <= x < 90:
                    item += t
                elif 90 <= x < 380:
                    desc += " " + t
                elif 380 <= x < 420:
                    material = t
                elif 420 <= x < 470:
                    qty = t.replace("[","").replace("]","")
                elif x >= 470:
                    part += t

            if item.strip().isdigit() and part.strip():
                results.append({
                    "Item": item.strip(),
                    "Description": desc.strip(),
                    "Material": material.strip() if material else "---",
                    "Quantity": qty.strip() if qty else "1",
                    "Part Number": part.strip()
                })

    return results


# RUN
data = extract_common_parts("manual_.pdf", 5)
print(json.dumps(data, indent=2))
