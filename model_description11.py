import pdfplumber
import re
import json
from pathlib import Path

PDF_FILE = Path("manual1.pdf")
PAGE_NUMBER = 2
OUTPUT_FILE = Path("output/model_description_chart_PX01X.json")
OUTPUT_FILE.parent.mkdir(exist_ok=True)

SECTION_SYNONYMS = {
    "Model Series": ["model series"],
    "Center Body Material": ["center body material"],
    "Connection": ["connection", "fluid connection"],
    "Fluid Caps / Manifold Material": [
        "fluid cap manifold material",
        "fluid caps manifold material",
        "fluid caps and manifold material",
        "fluid cap / manifold material"
    ],
    "Hardware Material": ["hardware material"],
    "Seat / Spacer Material": ["seat material", "seat spacer material"],
    "Ball Material": ["ball material", "check material"],
    "Diaphragm Material": ["diaphragm material", "diaphragm oring material"],
    "Revision": ["revision"],
    "Specialty Code 1": ["specialty code 1"],
    "Specialty Code 2": ["specialty code 2"]
}

VALID_SECTIONS = list(SECTION_SYNONYMS.keys())

# 🔥 FIXED REGEX
INLINE_CODE_DESC = re.compile(r"^\s*([A-Z0-9]{1,6})\s*[-–]\s*(.+)$")

def clean_line(text):
    if not text:
        return ""
    text = re.sub(r"\(cid:\d+\)", "", text)
    text = text.replace("\u2013", "-").replace("\u00ae", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize(text):
    text = text.lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return re.sub(r"\s+", " ", text).strip()

def is_layout_noise(line):
    if line.lower().startswith(("page ", "notice", "special testing")):
        return True
    if re.fullmatch(r"[X\- ]+", line):
        return True
    return False

def detect_section(line):
    norm = normalize(line)
    for canonical, variants in SECTION_SYNONYMS.items():
        for v in variants:
            if v in norm:
                return canonical
    return None

def extract_model_description_chart(pdf_path, page_number):
    chart = {s: {} for s in VALID_SECTIONS}
    current_section = None
    parsing_started = False

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        text = page.extract_text()

        for raw in text.splitlines():
            line = clean_line(raw)

            if not line or is_layout_noise(line):
                continue

            lower = line.lower()

            if "model description chart" in lower:
                parsing_started = True
                continue

            if not parsing_started:
                continue

            section = detect_section(line)
            if section:
                current_section = section
                continue

            if not current_section:
                continue

            m = INLINE_CODE_DESC.match(line)
            if m:
                code, desc = m.groups()
                chart[current_section][code] = desc.strip()

    return {k: v for k, v in chart.items() if v}

result = extract_model_description_chart(PDF_FILE, PAGE_NUMBER)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(json.dumps(result, indent=2, ensure_ascii=False))
