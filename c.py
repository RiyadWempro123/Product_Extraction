import pdfplumber
import re
import json

PDF_FILE = "manual3.pdf"

SECTIONS = [
    "Model Series",
    "Center Body Material",
    "CENTER BODY MATERIAL",
    "Connection",
    "Fluid Connection",
    "Fluid Caps / Manifold Material",
    "Fluid Caps And Manifold Material",
    "FLUID CAP / MANIFOLD MATERIAL",
    "Hardware Material",
    "Seat / Spacer Material",
    "DIAPHRAGM MATERIAL",
    "Seat Material",
    "SEAT MATERIAL",
    "Check Material",
    "Diaphragm / O-Ring Material",
    "Revision",
    "Specialty Code 1 (Blank if no Specialty Code)",
    "Specialty Code 2 (Blank if no Specialty Code)",
    "BALL MATERIAL"
   
]

CODE_DESC_REGEX = re.compile(r"^([A-Z0-9]{1,5})\s*-\s*(.+)$")

def clean_line(text):
    text = text.replace("((cid:31))", "")
    return text.strip()

def is_valid_code_desc(code, desc):
    if not code or not desc:
        return False
    if len(code) > 5:
        return False
    if not re.match(r'^[A-Z0-9]{1,5}$', code):
        return False
    desc_lower = desc.lower()
    if "page" in desc_lower or "xxx-xxx" in desc_lower:
        return False
    if re.search(r'[A-Z0-9]{2,5}-[A-Z0-9]{2,5}', desc):
        return False
    return True

def extract_chart(pdf_path):
    chart = {s: [] for s in SECTIONS}
    seen_codes = {s: set() for s in SECTIONS}
    current_section = None
    # print("chart", chart)
    # print("seen_codes", seen_codes)
   

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(1, 5):  # pages 2-5
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line = clean_line(line)
                # print("line 11", line)
                if not line:
                    continue

                # Detect section header
                if line in SECTIONS:
                    current_section = line
                    # print("current_section", current_section)
                    continue
                
                

                if current_section is None:
                    continue

                # Match CODE - Description
                match = CODE_DESC_REGEX.match(line)
                if match:
                    code, desc = match.groups()
                    code = code.strip()
                    desc = desc.strip()
                    # print(f"code : {code} -  desc {desc}")

                    if not is_valid_code_desc(code, desc):
                        continue  # skip unwanted lines

                    if code not in seen_codes[current_section]:
                        chart[current_section].append({"code": code, "description": desc})
                        seen_codes[current_section].add(code)
                   

    return chart


if __name__ == "__main__":
    chart = extract_chart(PDF_FILE)
    with open("chart.json", "w") as f:
        json.dump(chart, f, indent=2)
    print("Model Description Chart extracted successfully, unwanted entries removed!")
