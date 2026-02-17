# import pdfplumber

# with pdfplumber.open("manual.pdf") as pdf:
#     text = "\n".join(page.extract_text() for page in pdf.pages)
# print("Text", text)
# chunks = split_by_headers(text)

import pdfplumber

def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

text = extract_pdf_text("manual.pdf")
# print("Text", text)

import re

def extract_model_description_section(text):
    pattern = re.compile(
        r"MODEL DESCRIPTION CHART(.*?)Special Testing",
        re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(text)
    return match.group(1) if match else None

section = extract_model_description_section(text)

# print("Section", section)


def parse_model_series(section):
    pattern = re.findall(r"(PD01|PE01)-\s*(.+)", section)
    return [-
        {"code": code, "description": desc.strip()}
        for code, desc in pattern
    ]
def parse_center_body(section):
    pattern = re.findall(r"([EP])-?\s*(Groundable Polypropylene|Polypropylene)", section)
    return [
        {
            "code": code,
            "material": material,
            "hazardous_approved": "Groundable" in material
        }
        for code, material in pattern
    ]

def parse_seat_spacer(section):
    pattern = re.findall(r"([DKP012])-\s*(.+)", section)
    seen = set()
    results = []
    for code, desc in pattern:
        if code not in seen:
            seen.add(code)
            results.append({"code": code, "material": desc.strip()})
    return results

model_description_chart = {
    "model_series": parse_model_series(section),
    "center_body_material": parse_center_body(section),
    "seat_spacer_material": parse_seat_spacer(section)
}

import json
print(json.dumps(model_description_chart, indent=2))
