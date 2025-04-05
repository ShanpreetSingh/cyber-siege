import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import email
from email.policy import default

# Configure Tesseract OCR path if needed (uncomment and modify for your system)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class BillProcessor:
    """Automated system for processing bills from various sources."""
    
    def __init__(self):
        self.output_columns = [
            'vendor_name',
            'bill_number',
            'billing_date',
            'due_date',
            'total_amount',
            'line_items'
        ]

    def process_files(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Process multiple files and return extracted data as a DataFrame.
        
        Args:
            file_paths: List of paths to invoice files
            
        Returns:
            DataFrame containing extracted invoice data
        """
        processed_data = []
        
        for file_path in file_paths:
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext == '.eml':
                    extracted_data = self._process_email(file_path)
                elif file_ext == '.pdf':
                    extracted_data = self._process_pdf(file_path)
                elif file_ext in ('.jpg', '.jpeg', '.png', '.tiff'):
                    extracted_data = self._process_image(file_path)
                elif file_ext in ('.xml', '.edi', '.csv'):
                    extracted_data = self._process_digital_invoice(file_path)
                else:
                    print(f"Unsupported file type: {file_path}")
                    continue
                
                if extracted_data:
                    processed_data.append(extracted_data)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue
                
        return pd.DataFrame(processed_data, columns=self.output_columns)
    
    def _process_email(self, email_path: str) -> Optional[Dict]:
        """Process email and its attachments."""
        with open(email_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=default)
        
        extracted_data = None
        
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            filename = part.get_filename()
            if filename:
                file_ext = os.path.splitext(filename)[1].lower()
                temp_path = f"temp{file_ext}"
                
                with open(temp_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                try:
                    if file_ext == '.pdf':
                        extracted_data = self._process_pdf(temp_path)
                    elif file_ext in ('.jpg', '.jpeg', '.png', '.tiff'):
                        extracted_data = self._process_image(temp_path)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        
        return extracted_data
    
    def _process_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Process PDF file (both text-based and scanned)."""
        try:
            # First try direct text extraction
            text = self._extract_text_from_pdf(pdf_path)
            if not text.strip():
                # Fall back to OCR if no text found
                images = convert_from_path(pdf_path)
                text = ' '.join(pytesseract.image_to_string(img) for img in images)
            
            return self._parse_invoice_text(text)
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return None
    
    def _process_image(self, image_path: str) -> Optional[Dict]:
        """Process scanned image using OCR."""
        try:
            text = pytesseract.image_to_string(image_path)
            return self._parse_invoice_text(text)
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def _process_digital_invoice(self, file_path: str) -> Optional[Dict]:
        """Process structured digital invoices (EDI, XML, CSV)."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                return self._parse_csv_invoice(file_path)
            elif file_ext == '.xml':
                return self._parse_xml_invoice(file_path)
            elif file_ext == '.edi':
                return self._parse_edi_invoice(file_path)
        except Exception as e:
            print(f"Error processing digital invoice {file_path}: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from text-based PDF."""
        # This is a placeholder - in production you might use PyPDF2 or pdfplumber
        return ""
    
    def _parse_invoice_text(self, text: str) -> Dict:
        """Parse extracted text to find invoice fields."""
        # This is a simplified version - real implementation would be more robust
        data = {
            'vendor_name': self._extract_vendor_name(text),
            'bill_number': self._extract_bill_number(text),
            'billing_date': self._extract_date(text, 'invoice date'),
            'due_date': self._extract_date(text, 'due date'),
            'total_amount': self._extract_total_amount(text),
            'line_items': self._extract_line_items(text)
        }
        return data
    
    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor name from text."""
        # Simple regex - would need customization based on actual invoices
        match = re.search(r'(?:from|vendor|supplier)[:\s]*(.*?)\n', text, re.I)
        return match.group(1).strip() if match else "Unknown Vendor"
    
    def _extract_bill_number(self, text: str) -> str:
        """Extract invoice number from text."""
        match = re.search(r'(?:invoice\s*#?|bill\s*number)[:\s]*([A-Z0-9-]+)', text, re.I)
        return match.group(1) if match else "Unknown"
    
    def _extract_date(self, text: str, date_type: str) -> str:
        """Extract date from text based on date type."""
        match = re.search(fr'{date_type}[:\s]*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})', text, re.I)
        if match:
            try:
                date_str = match.group(1)
                return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return date_str
        return ""
    
    def _extract_total_amount(self, text: str) -> float:
        """Extract total amount from text."""
        match = re.search(r'total\s*(?:amount)?[:\s]*\$?(\d+\.\d{2})', text, re.I)
        return float(match.group(1)) if match else 0.0
    
    def _extract_line_items(self, text: str) -> str:
        """Extract line items from text."""
        # Simplified - real implementation would parse line items properly
        matches = re.findall(r'(\d+)\s+(.*?)\s+\$?(\d+\.\d{2})', text)
        return "; ".join(f"{qty} x {desc} @ {price}" for qty, desc, price in matches)
    
    def _parse_csv_invoice(self, file_path: str) -> Dict:
        """Parse CSV invoice format."""
        # Implementation would depend on specific CSV format
        return {}
    
    def _parse_xml_invoice(self, file_path: str) -> Dict:
        """Parse XML invoice format."""
        # Implementation would depend on specific XML schema
        return {}
    
    def _parse_edi_invoice(self, file_path: str) -> Dict:
        """Parse EDI invoice format."""
        # Implementation would depend on specific EDI format
        return {}


# Example usage
if __name__ == "__main__":
    processor = BillProcessor()
    
    # Example file paths (replace with actual paths)
    sample_files = [
        'invoice.pdf',
        'scanned_invoice.jpg',
        'email_invoice.eml',
        'digital_invoice.xml'
    ]
    
    # Process files and save to CSV
    result_df = processor.process_files(sample_files)
    result_df.to_csv('processed_invoices.csv', index=False)
    print("Processing complete. Results saved to processed_invoices.csv")