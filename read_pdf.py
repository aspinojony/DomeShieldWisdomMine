import sys
from pypdf import PdfReader

def extract_text(pdf_path, out_path):
    reader = PdfReader(pdf_path)
    with open(out_path, 'w', encoding='utf-8') as f:
        for i, page in enumerate(reader.pages):
            f.write(f"--- PAGE {i+1} ---\n")
            text = page.extract_text()
            if text:
                f.write(text)
            f.write("\n\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python read_pdf.py <pdf_path> <out_path>")
        sys.exit(1)
    extract_text(sys.argv[1], sys.argv[2])
