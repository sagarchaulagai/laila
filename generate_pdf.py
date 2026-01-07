import os
import glob
import sys
import traceback
from fpdf import FPDF

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = "All_Questions.pdf"

class PDF(FPDF):
    def header(self):
        # Use built-in font for header to be safe, or the added font if available
        # But header is called before we might have added the font in the main block if we are not careful.
        # However, FPDF class structure initializes before add_page.
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Compiled Question Texts', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def create_pdf():
    try:
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add a Unicode font
        font_path = r"C:\Windows\Fonts\arial.ttf"
        font_name = "MyArial"
        if os.path.exists(font_path):
            print(f"Loading font from {font_path}")
            pdf.add_font(font_name, "", font_path)
            pdf.set_font(font_name, size=11)
        else:
            print("Font not found, using Helvetica (non-unicode)")
            pdf.set_font("helvetica", size=11)
            
        pdf.add_page()

        folders = sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(d) and d.isdigit()], key=int)
        
        for folder in folders:
            dir_path = os.path.join(BASE_DIR, folder)
            files = glob.glob(os.path.join(dir_path, "*.txt"))
            files.sort()
            
            for filepath in files:
                filename = os.path.basename(filepath)
                name, ext = os.path.splitext(filename)
                
                # Header format: 1a) -------------
                header_text = f"{name}) -------------"
                
                print(f"Processing {filename}...")
                
                # Add separation space
                pdf.ln(5)
                
                # Write Header
                # Switch to Bold if possible. Since we added only Regular style for MyArial, 
                # we can't switch to Bold unless we add it or use core font.
                # Let's just use the current font.
                pdf.cell(0, 10, header_text, new_x="LMARGIN", new_y="NEXT")
                
                # Read content
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Normalize line endings
                    content = content.replace('\r\n', '\n')
                    
                    # Write Content
                    # If using core font, we must replace non-latin1 chars
                    # If using MyArial, it should handle most.
                    pdf.multi_cell(0, 5, content)
                    pdf.ln(5)
                    
                except Exception as e:
                    print(f"Error reading/writing {filename}: {e}")
                    traceback.print_exc()

        output_path = os.path.join(BASE_DIR, OUTPUT_PDF)
        pdf.output(output_path)
        print(f"PDF generated successfully: {output_path}")
        
    except Exception as e:
        print("Fatal error:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_pdf()
