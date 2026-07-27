import fitz  # pymupdf
import os

def extract_native(pdf_path, output_path=None):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)

    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + ".txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    return output_path

if __name__ == "__main__":
    pdf_path = input("PDF file path: ").strip()
    out = extract_native(pdf_path)
    print(f"Saved to {out}")