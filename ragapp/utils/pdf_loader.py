# ragapp/utils/pdf_loader.py
import PyPDF2
import logging

logger = logging.getLogger(__name__)

def extract_pdf_text_with_pages(pdf_path):
    """Extract text from PDF with page numbers"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():  # Only yield pages with text
                    yield page_num + 1, text
                    
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

class PDFLoader:
    @staticmethod
    def extract_text_from_pdf(file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise Exception(f"Error reading PDF: {str(e)}")
        
        if not text.strip():
            raise Exception("No text could be extracted from the PDF")
        
        return text