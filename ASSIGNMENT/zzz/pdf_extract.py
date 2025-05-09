import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar, LTAnno


def extract_font_segments(pdf_path):

    segments = []

    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        current_size = None
                        buffer = []

                        for char in text_line:
                            if isinstance(char, LTChar):
                                size = char.size
                                if current_size is None:
                                    current_size = size
                                    buffer = [char.get_text()]
                                elif size == current_size:
                                    buffer.append(char.get_text())
                                else:
                                    segments.append({'size': current_size, 'text': ''.join(buffer)})
                                    current_size = size
                                    buffer = [char.get_text()]
                            elif isinstance(char, LTAnno):
                                buffer.append(char.get_text())

                        # Flush remaining buffer
                        if buffer and current_size is not None:
                            segments.append({'size': current_size, 'text': ''.join(buffer)})

    return segments


def main():
    pdf_path = r"C:\\Users\\guian\Desktop\\ASSIGNMENT\\PDF\\Document_5.pdf"
    out_path = r'C:\\Users\\guian\\Desktop\\ASSIGNMENT\\PDF_results\\pdf_extract.json'

    result = extract_font_segments(pdf_path)

    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Results written to {out_path}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
