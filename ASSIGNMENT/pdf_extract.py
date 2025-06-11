import json
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar, LTAnno

def extract_font_segments(pdf_path):
    """Extract font segments from PDF with encoding cleanup"""
    segments = []
    page_number = 1

    # Helper function for cleaning text encoding
    def clean_text_encoding(text):
        if not text:
            return ""
        
        try:
            # Handle encoding issues
            cleaned = text.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Replace problematic unicode characters
            replacements = {
                '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
                '\u2013': '-', '\u2014': '--', '\u00a0': ' ', '\u2026': '...',
                '\ufeff': '',
            }
            
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            
            # Removing non printable chars
            cleaned = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned)
            
            return cleaned
            
        except (UnicodeDecodeError, UnicodeEncodeError) as e:
            print(f"Encoding error: {e}")
            return ''.join(char for char in text if ord(char) < 128)

    try:
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            current_size = None
                            current_font = None
                            buffer = []

                            for char in text_line:
                                if isinstance(char, LTChar):
                                    try:
                                        size = round(char.size, 1)
                                        font = char.fontname or "Unknown"
                                        char_text = clean_text_encoding(char.get_text())
                                        
                                        if current_size is None:
                                            current_size = size
                                            current_font = font
                                            buffer = [char_text]
                                        elif size == current_size and font == current_font:
                                            buffer.append(char_text)
                                        else:
                                            if buffer:
                                                segments.append({
                                                    'text': ''.join(buffer),
                                                    'size': current_size, 
                                                    'font': current_font,
                                                    'page': page_number
                                                })
                                            current_size = size
                                            current_font = font
                                            buffer = [char_text]
                                    except Exception as e:
                                        print(f"Error processing character: {e}")
                                        continue
                                        
                                elif isinstance(char, LTAnno):
                                    try:
                                        anno_text = clean_text_encoding(char.get_text())
                                        buffer.append(anno_text)
                                    except Exception as e:
                                        print(f"Error processing annotation: {e}")
                                        continue

                            # Flush remaining buffer
                            if buffer and current_size is not None:
                                segments.append({
                                    'text': ''.join(buffer),
                                    'size': current_size,
                                    'font': current_font,
                                    'page': page_number
                                })
            
            page_number += 1
            
    except Exception as e:
        print(f"Error extracting from PDF: {e}")
        return []

    return segments

def str_to_latex(segments):
    """Convert font segments to LaTeX focusing on sections, subsections and main text"""
    latex_parts = []
    
    #function for latex
    def escape_latex(text):
        if not text:
            return ""
        
        try:
            # Handle encoding issues first
            cleaned = text.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Replace problematic unicode characters
            replacements = {
                '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
                '\u2013': '-', '\u2014': '--', '\u00a0': ' ', '\u2026': '...',
                '\ufeff': '',
            }
            
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            
            # Remove non-printable characters except newlines and tabs
            cleaned = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned)
            
            # LaTeX escaping - backslash must be first!
            latex_replacements = {
                '\\': '\\textbackslash{}',
                '{': '\\{',
                '}': '\\}',
                '$': '\\$',
                '&': '\\&',
                '%': '\\%',
                '#': '\\#',
                '^': '\\textasciicircum{}',
                '_': '\\_',
                '~': '\\textasciitilde{}'
            }
            
            for char, replacement in latex_replacements.items():
                cleaned = cleaned.replace(char, replacement)
            
            return cleaned
            
        except (UnicodeDecodeError, UnicodeEncodeError) as e:
            print(f"Encoding error: {e}")
            return ''.join(char for char in text if ord(char) < 128)
    
    # Process segments
    for segment in segments:
        try:
            text = segment.get('text', '')
            size = segment.get('size', 12)
            
            # Skip empty or whitespace-only segments
            if not text or text.isspace():
                continue
            
            # Clean the text - remove \n and extra whitespace
            clean_text = text.replace('\n', ' ').strip()
            if not clean_text:
                continue
            
            # Escape LaTeX characters
            escaped_text = escape_latex(clean_text)
            if not escaped_text:
                continue
            
            # Find closest font size to our target sizes
            target_sizes = [28, 18, 12]
            closest_size = min(target_sizes, key=lambda x: abs(x - size))
            
            # Create LaTeX commands based on font size
            # Large fonts (28pt) -> sections
            # Medium fonts (18pt) -> subsections  
            # Small fonts (12pt) -> regular text


            if closest_size == 28:
                latex_parts.append(f"\\section{{{escaped_text}}}")
            elif closest_size == 18:
                latex_parts.append(f"\\subsection{{{escaped_text}}}")
            elif closest_size == 12:
                latex_parts.append(escaped_text)
                
        except Exception as e:
            print(f"Error processing segment: {e}")
            continue
    
    return '\n'.join(latex_parts)


if __name__ == "__main__":
    # TESTE
    sigma = extract_font_segments(r'C:\Users\guian\Desktop\ASSIGNMENT\PDF\math_IA_guilherme_albernaz_pedro_albernaz (1).pdf')
    
    print("Extracted segments:")
    for i, segment in enumerate(sigma[:10]): 
        print(f"{i+1}: {segment}")
    
    print("\n" + "="*50)
    print("LaTeX Output:")
    
    #
    latex_result = str_to_latex(sigma)
    print(latex_result)
    
    print(f"Total segments processed: {len(sigma)}")
