import glob
import pdfplumber
import os
import re
import json

CVS_DIR = "CVs_FIN-002_2025-12-10"
OUTPUT_JSON = "extracted_companies.json"

def extract_companies_from_text(text):
    """
    Heuristic extraction of company names.
    """
    companies = set()
    
    # 1. Look for legal suffixes (Chile/Latam context)
    # Matches "Name S.A.", "Name SpA", etc.
    # We look for Capitalized words preceding the suffix.
    suffix_pattern = r"([A-ZÁÉÍÓÚÑ][a-zA-Záéíóúñ0-9\s&]+(?:\sS\.?A\.?|\sSpA|\sLtda\.?|\sLimitada|\sInc\.?|\sCorp\.?|\sGroup|\sGrupo))"
    matches = re.findall(suffix_pattern, text)
    for m in matches:
        # cleanup: take last 4-5 words max to avoid capturing full sentences
        words = m.split()
        if len(words) < 6:
            companies.add(m.strip())

    # 2. Look for "Company | Role" or "Role | Company" patterns (often used in headers)
    # Matches "Something | Something"
    pipe_pattern = r"([A-ZÁÉÍÓÚÑ][a-zA-Záéíóúñ\s]+)\s\|\s([A-ZÁÉÍÓÚÑ][a-zA-Záéíóúñ\s]+)"
    pipe_matches = re.findall(pipe_pattern, text)
    for m in pipe_matches:
        # Try to guess which side is the company (often shorter or has legal suffix, but hard to know)
        # We'll add both as candidates if they are short enough
        if len(m[0].split()) < 5: companies.add(m[0].strip())
        if len(m[1].split()) < 5: companies.add(m[1].strip())
        
    return list(companies)

def main():
    pdf_files = glob.glob(os.path.join(CVS_DIR, "*.pdf"))
    all_companies = {}
    
    print(f"Scanning {len(pdf_files)} CVs...")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    extract = page.extract_text()
                    if extract: text += extract + "\n"
            
            candidates = extract_companies_from_text(text)
            if candidates:
                all_companies[filename] = candidates
                print(f"  {filename}: Found {len(candidates)} candidates ({', '.join(candidates)})")
            else:
                print(f"  {filename}: No obvious companies found.")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    with open(OUTPUT_JSON, "w", encoding='utf-8') as f:
        json.dump(all_companies, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtraction complete. Saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
