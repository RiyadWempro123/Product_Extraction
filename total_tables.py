import pdfplumber
import pandas as pd
from pathlib import Path

def extract_actual_tables(pdf_path, output_dir="output_tables"):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    

    table_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            # Extract table(s) using pdfplumber's table extraction
            # Settings like 'vertical_strategy' and 'horizontal_strategy' help detect lines
            tables = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_tolerance": 5
                }
            )

            for t_idx, table in enumerate(tables, start=1):
                if not table or len(table) < 2:
                    continue

                # Convert to DataFrame
                df = pd.DataFrame(table[1:], columns=table[0])

                table_count += 1
                # Save CSV
                csv_path = output_dir / f"page_{page_no}_table_{table_count}.csv"
                df.to_csv(csv_path, index=False)
                print(f"Saved table {table_count} from page {page_no}")

    print(f"\n✅ Extraction complete — {table_count} tables saved.")

if __name__ == "__main__":
    extract_actual_tables("PX03P.pdf")
