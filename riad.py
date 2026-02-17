import pdfplumber
import re
import json
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

PDF_FILE = Path("manual.pdf")  # Input PDF
OUTPUT_FILE = Path("output/model_description_chart.json")
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ---------------------------------------------------
# Section normalization
# ---------------------------------------------------

SECTION_MAP = {
    "model series": "Model Series",
    "center body material": "Center Body Material",
    "connection": "Connection",
    "fluid caps / manifold material": "Fluid Caps / Manifold Material",
    "hardware material": "Hardware Material",
    "seat / spacer material": "Seat / Spacer Material",
    "check material": "Check Material",
    "diaphragm / o-ring material": "Diaphragm / O-Ring Material",
    "revision": "Revision",
    "specialty code 1 (blank if no specialty code)": "Specialty Code 1",
    "specialty code 2 (blank if no specialty code)": "Specialty Code 2",
}

VALID_SECTIONS = list(SECTION_MAP.values())

# ---------------------------------------------------
# Regex for CODE - Description
# ---------------------------------------------------

CODE_DESC_REGEX = re.compile(r"^\s*([A-Z0-9]{1,5})\s*[-–]\s*(.+)$")

# ---------------------------------------------------
# Clean PDF text
# ---------------------------------------------------

def clean_line(text):
    if not text:
        return ""
    text = re.sub(r"\(\(cid:\d+\)\)", "", text)
    text = re.sub(r"\(cid:\d+\)", "", text)
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ---------------------------------------------------
# Validate a chart entry based on section
# ---------------------------------------------------

def is_valid_entry(section, code, desc):
    desc_lower = desc.lower()
    bad_words = [
        "page", "xxx-xxx", "air section", "fluid section",
        "dimension", "mm", "ptf", "bsp", "nptf",
        "en)", "px01x", "pd01x", "pe01x"
    ]
    if any(bad in desc_lower for bad in bad_words):
        return False

    # Section-specific rules
    if section == "Model Series":
        return bool(re.fullmatch(r"P[DE]01", code))
    if section == "Connection":
        return code == "H"
    if section == "Revision":
        return code == "A"
    if section in ["Specialty Code 1", "Specialty Code 2"]:
        return bool(re.fullmatch(r"[A-Z0-9]", code))
    # Other sections: allow alphanumeric single character codes
    return bool(re.fullmatch(r"[A-Z0-9]", code))

# ---------------------------------------------------
# Extract chart from PDF
# ---------------------------------------------------

def extract_model_description_chart(pdf_path):
    chart = {s: [] for s in VALID_SECTIONS}
    seen = {s: set() for s in VALID_SECTIONS}
    current_section = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for raw_line in text.splitlines():
                line = clean_line(raw_line)
                if not line:
                    continue

                normalized = line.lower()

                # Detect section headers
                if normalized in SECTION_MAP:
                    current_section = SECTION_MAP[normalized]
                    continue

                if not current_section:
                    continue

                # Match code-description
                match = CODE_DESC_REGEX.match(line)
                if not match:
                    continue

                code, desc = match.groups()
                code, desc = code.strip(), desc.strip()

                if not is_valid_entry(current_section, code, desc):
                    continue

                # Deduplicate
                if code in seen[current_section]:
                    continue

                chart[current_section].append({"code": code, "description": desc})
                seen[current_section].add(code)

    # Remove empty sections
    chart = {k: v for k, v in chart.items() if v}
    return chart

# ---------------------------------------------------
# Run
# ---------------------------------------------------

if __name__ == "__main__":
    if not PDF_FILE.exists():
        print(f"❌ PDF file not found: {PDF_FILE}")
    else:
        final_chart = extract_model_description_chart(PDF_FILE)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_chart, f, indent=2)
        print(f"✅ Model Description Chart extracted successfully to {OUTPUT_FILE}")
