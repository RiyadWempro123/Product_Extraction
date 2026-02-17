# import pytesseract
# from PIL import Image
# import json
# import re

# # -----------------------------
# # STEP 1: OCR FROM IMAGE
# # -----------------------------
# img = Image.open("manual_pages/page_2.png")
# raw_text = pytesseract.image_to_string(img, lang="eng")

# # Optional: see OCR output
# # print(raw_text)


# # -----------------------------
# # STEP 2: SECTION DEFINITIONS
# # -----------------------------
# SECTION_MAP = {
#     "model series": "model_series",
#     "center body material": "center_body_material",
#     "connection": "connection",
#     "fluid caps / manifold material": "fluid_caps_manifold_material",
#     "hardware material": "hardware_material",
#     "seat / spacer material": "seat_spacer_material",
#     "check material": "check_material",
#     "diaphragm / o-ring material": "diaphragm_o_ring_material",
#     "revision": "revision",
#     "specialty code 1": "specialty_code_1",
#     "specialty code 2": "specialty_code_2"
# }

# # Initialize output
# json_data = {v: {} for v in SECTION_MAP.values()}
# current_section = None


# # -----------------------------
# # STEP 3: PARSE OCR TEXT
# # -----------------------------
# for line in raw_text.splitlines():
#     line = line.strip()
#     if not line:
#         continue

#     lower_line = line.lower()

#     # Detect section headers
#     for header, section_name in SECTION_MAP.items():
#         if lower_line.startswith(header):
#             current_section = section_name
#             break
#     else:
#         # Parse CODE - Description
#         if current_section:
#             match = re.match(r"^([A-Z0-9]+)\s*-\s*(.+)$", line)
#             if not match:
#                 continue

#             code, desc = match.groups()

#             entry = {
#                 "description": desc.replace("(*)", "").strip()
#             }

#             # Hazardous detection
#             if "(*)" in desc:
#                 entry["hazardous_ok"] = True

#             # Flex check detection
#             if "flex check only" in desc.lower():
#                 entry["flex_check_only"] = True

#             json_data[current_section][code] = entry


# # -----------------------------
# # STEP 4: ADD NOTES
# # -----------------------------
# json_data["notes"] = {
#     "hazardous_location_rule": (
#         "Only options marked as hazardous_ok true are acceptable for hazardous locations. "
#         "Certain combinations may not be possible."
#     ),
#     "source": "PX01 Model Description Chart – Page 2 of 12"
# }


# # -----------------------------
# # STEP 5: SAVE JSON
# # -----------------------------
# with open("model_description_chart.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, indent=2, ensure_ascii=False)

# print("✅ JSON successfully generated: model_description_chart.json")
import pytesseract
from PIL import Image
import json
import re

# -----------------------------
# STEP 1: OCR FROM IMAGE
# -----------------------------
img = Image.open("manual_pages/page_2.png")
raw_text = pytesseract.image_to_string(img, lang="eng")

# Optional: see OCR output
# print(raw_text)


# -----------------------------
# STEP 2: SECTION DEFINITIONS
# -----------------------------
SECTION_MAP = {
    "model series": "model_series",
    "center body material": "center_body_material",
    "connection": "connection",
    "fluid caps / manifold material": "fluid_caps_manifold_material",
    "hardware material": "hardware_material",
    "seat / spacer material": "seat_spacer_material",
    "check material": "check_material",
    "diaphragm / o-ring material": "diaphragm_o_ring_material",
    "revision": "revision",
    "specialty code 1": "specialty_code_1",
    "specialty code 2": "specialty_code_2"
}

# Initialize output
json_data = {v: {} for v in SECTION_MAP.values()}
current_section = None


# -----------------------------
# STEP 3: PARSE OCR TEXT
# -----------------------------
for line in raw_text.splitlines():
    line = line.strip()
    if not line:
        continue

    lower_line = line.lower()

    # Detect section headers
    for header, section_name in SECTION_MAP.items():
        if lower_line.startswith(header):
            current_section = section_name
            break
    else:
        # Parse CODE - Description
        if current_section:
            match = re.match(r"^([A-Z0-9]+)\s*-\s*(.+)$", line)
            if not match:
                continue

            code, desc = match.groups()

            entry = {
                "description": desc.replace("(*)", "").strip()
            }

            # Hazardous detection
            if "(*)" in desc:
                entry["hazardous_ok"] = True

            # Flex check detection
            if "flex check only" in desc.lower():
                entry["flex_check_only"] = True

            json_data[current_section][code] = entry


# -----------------------------
# STEP 4: ADD NOTES
# -----------------------------
json_data["notes"] = {
    "hazardous_location_rule": (
        "Only options marked as hazardous_ok true are acceptable for hazardous locations. "
        "Certain combinations may not be possible."
    ),
    "source": "PX01 Model Description Chart – Page 2 of 12"
}


# -----------------------------
# STEP 5: SAVE JSON
# -----------------------------
with open("model_description_chart.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print("✅ JSON successfully generated: model_description_chart.json")
