import pdfplumber
import re
import json

PDF_FILE = "manual.pdf"

def extract_common_parts(pdf_path):
    parts = []

    with pdfplumber.open(pdf_path) as pdf:
        # Step 1: Reconstruct lines from words (handles PDFs with weird line breaks)
        full_text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            words = page.extract_words()
            # Group words by 'top' coordinate to reconstruct lines
            lines_dict = {}
            for w in words:
                top = round(float(w['top']))
                lines_dict.setdefault(top, []).append(w['text'])
            lines = [" ".join(sorted(lines_dict[top], key=lambda x: x)) for top in sorted(lines_dict.keys())]
            full_text += "\n".join(lines) + "\n"

    # Step 2: Find COMMON PARTS block
    m_block = re.search(r'COMMON PARTS(.*?)(FLUID CONNECTION|PX01X-|MODEL|$)', full_text, re.IGNORECASE | re.DOTALL)
    if not m_block:
        print("COMMON PARTS block not found!")
        return []

    block_text = m_block.group(1)

    # Step 3: Extract material codes
    material_map = {}
    mat_pattern = re.compile(r'\[([A-Za-z0-9]+)\]\s*=\s*(.+)')
    filtered_lines = []
    for line in block_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = mat_pattern.match(line)
        if m:
            code, name = m.groups()
            material_map[code.strip()] = name.strip()
        else:
            filtered_lines.append(line)

    # Step 4: Parse part rows (multi-line description)
    part_buffer = []
    for line in filtered_lines:
        # Detect line with quantity + part number
        m_qty = re.search(r'\[?(\d+)\]?\s+([A-Z0-9\-]+)$', line)
        if m_qty:
            qty, part_no = m_qty.groups()
            # Combine previous lines as description
            description_text = " ".join(part_buffer).strip()
            # Extract item number
            m_item = re.match(r'^(\d+)', description_text)
            item_number = int(m_item.group(1)) if m_item else None
            if item_number:
                description_text = re.sub(r'^\d+\s*', '', description_text)
            # Extract material code if present
            mat_match = re.search(r'\[([A-Za-z0-9]+)\]', " ".join(part_buffer + [line]))
            material_code = mat_match.group(1) if mat_match else None
            material_name = material_map.get(material_code, material_code) if material_code else None

            parts.append({
                "item": item_number,
                "description": description_text,
                "material": material_name,
                "qty": int(qty),
                "part_no": part_no
            })
            part_buffer = []
        else:
            part_buffer.append(line)

    return parts

if __name__ == "__main__":
    common_parts = extract_common_parts(PDF_FILE)
    print("COMMON PARTS extracted:")
    print(json.dumps(common_parts, indent=2))
