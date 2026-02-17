import re
import pdfplumber
from typing import List, Dict

# =========================
# REGEX PATTERNS
# =========================

EXP_MODEL_REGEX = re.compile(
    r"PX\d{2}[A-Z]-[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z][A-Z0-9]{3}"
)

PRO_MODEL_REGEX = re.compile(
    r"666\d[A-Z0-9]{2,3}-[A-Z0-9]{2,3}-[A-Z]"
)

# =========================
# PDF TEXT EXTRACTION
# =========================

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# =========================
# MODEL EXTRACTION
# =========================

def extract_models(text: str) -> Dict[str, List[str]]:
    exp_models = set(EXP_MODEL_REGEX.findall(text))
    pro_models = set(PRO_MODEL_REGEX.findall(text))

    return {
        "EXP": list(exp_models),
        "PRO": list(pro_models)
    }


# =========================
# PARSERS
# =========================

def parse_exp_model(model: str) -> Dict:
    """
    Example: PX15P-HDS-PGX-AXEX
    """
    return {
        "model_code": model,
        "series": "EXP",
        "prefix": model[0:2],                # PX
        "pump_size": model[2:4],             # 15
        "body_variant": model[4],            # P / X
        "connection_block": model[6:9],      # HDS
        "material_block": model[10:13],      # PGX
        "revision": model[14],               # A
        "specialty_block": model[15:18]      # XEX
    }


def parse_pro_model(model: str) -> Dict:
    """
    Example: 6661XX-XXX-C
    """
    base, mid, rev = model.split("-")

    return {
        "model_code": model,
        "series": "PRO",
        "family": base[:3],                  # 666
        "pump_type": base[3],                # 1 / 2
        "body_configuration": base[4:],      # XX / XXX
        "material_configuration": mid,       # XX / XXX
        "revision": rev                      # C
    }


# =========================
# NORMALIZATION
# =========================

def normalize_models(models: Dict[str, List[str]]) -> List[Dict]:
    normalized = []

    for model in models.get("EXP", []):
        normalized.append(parse_exp_model(model))

    for model in models.get("PRO", []):
        normalized.append(parse_pro_model(model))

    return normalized


# =========================
# MAIN PIPELINE
# =========================

def extract_and_parse_models(pdf_path: str) -> List[Dict]:
    text = extract_text_from_pdf(pdf_path)
    models = extract_models(text)
    return normalize_models(models)



results = extract_and_parse_models("pro_series.pdf")

for r in results:
    print(r)
