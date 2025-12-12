import glob
import pdfplumber
import os

CVS_DIR = "CVs_FIN-002_2025-12-10"

def inspect_layout():
    pdf_files = glob.glob(os.path.join(CVS_DIR, "*.pdf"))[:3] # Check first 3
    for pdf_path in pdf_files:
        print(f"\n--- {os.path.basename(pdf_path)} ---")
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            # Print first 1000 chars with layout
            print(first_page.extract_text()[:1000])

if __name__ == "__main__":
    inspect_layout()
