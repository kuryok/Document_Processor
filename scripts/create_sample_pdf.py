import fitz

def create_sample_pdf(filename="sample.pdf"):
    doc = fitz.open()
    
    # Page 1: Normal text with a title and paragraph
    page1 = doc.new_page()
    page1.insert_text((50, 50), "1. Introduction to the Document", fontsize=20)
    page1.insert_text((50, 100), "This is a sample document for testing the doc_preprocessor pipeline.", fontsize=12)
    page1.insert_text((50, 120), "We want to ensure that native PyMuPDF extraction works correctly.", fontsize=12)
    page1.insert_text((50, 750), "Page 1", fontsize=10) # Footer
    
    # Page 2: Another page with list and footer
    page2 = doc.new_page()
    page2.insert_text((50, 50), "2. Features", fontsize=16)
    page2.insert_text((50, 100), "• Decoupled pipeline", fontsize=12)
    page2.insert_text((50, 120), "• High quality output", fontsize=12)
    page2.insert_text((50, 750), "Page 2", fontsize=10) # Footer
    
    doc.save(filename)
    doc.close()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_sample_pdf()
