import os
import re
from typing import List, Dict, Optional
import PyPDF2
from docx import Document
import pandas as pd
from pathlib import Path

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt', '.csv']
        self.document_types = {
            'pay_stub': ['pay stub', 'paystub', 'earnings', 'salary'],
            'bank_statement': ['bank statement', 'checking', 'savings', 'account statement'],
            'tax_return': ['1040', 'tax return', 'w2', 'w-2', '1099'],
            'application': ['loan application', '1003', 'uniform residential'],
            'employment_verification': ['voe', 'employment verification', 'employer'],
            'asset_verification': ['vod', 'deposit verification', 'asset verification'],
            'appraisal': ['appraisal', 'property value', 'home value'],
            'title_report': ['title', 'title report', 'title commitment']
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading TXT: {str(e)}"

    def process_document(self, file_path: str) -> Dict:
        """Process a single document and return structured data"""
        file_extension = Path(file_path).suffix.lower()

        if file_extension not in self.supported_formats:
            return {
                'error': f'Unsupported file format: {file_extension}',
                'text': '',
                'type': 'unknown'
            }

        # Extract text based on file type
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            text = "Unsupported format"

        # Classify document type
        doc_type = self.classify_document(text, Path(file_path).name)

        return {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'text': text,
            'type': doc_type,
            'word_count': len(text.split()),
            'error': None
        }

    def classify_document(self, text: str, filename: str) -> str:
        """Classify document type based on content and filename"""
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Check filename first
        for doc_type, keywords in self.document_types.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return doc_type

        # Check content
        for doc_type, keywords in self.document_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return doc_type

        return 'unknown'

    def extract_key_data(self, doc_data: Dict) -> Dict:
        """Extract key financial data from documents"""
        text = doc_data['text'].lower()
        doc_type = doc_data['type']

        extracted_data = {
            'amounts': self._extract_amounts(text),
            'dates': self._extract_dates(text),
            'ssn': self._extract_ssn(text),
            'names': self._extract_names(text)
        }

        # Type-specific extractions
        if doc_type == 'pay_stub':
            extracted_data.update(self._extract_paystub_data(text))
        elif doc_type == 'bank_statement':
            extracted_data.update(self._extract_bank_statement_data(text))
        elif doc_type == 'tax_return':
            extracted_data.update(self._extract_tax_data(text))

        return extracted_data

    def _extract_amounts(self, text: str) -> List[float]:
        """Extract monetary amounts from text"""
        amount_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.findall(amount_pattern, text)
        return [float(amount.replace('$', '').replace(',', '')) for amount in amounts]

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\w+ \d{1,2}, \d{4}'
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        return dates

    def _extract_ssn(self, text: str) -> List[str]:
        """Extract SSN patterns (for identification, not storage)"""
        ssn_pattern = r'\d{3}-\d{2}-\d{4}'
        return re.findall(ssn_pattern, text)

    def _extract_names(self, text: str) -> List[str]:
        """Extract potential names (basic pattern)"""
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        return re.findall(name_pattern, text)

    def _extract_paystub_data(self, text: str) -> Dict:
        """Extract specific data from pay stubs"""
        return {
            'gross_pay': self._find_amount_near_keyword(text, ['gross pay', 'gross income']),
            'net_pay': self._find_amount_near_keyword(text, ['net pay', 'take home']),
            'ytd_gross': self._find_amount_near_keyword(text, ['ytd gross', 'year to date'])
        }

    def _extract_bank_statement_data(self, text: str) -> Dict:
        """Extract specific data from bank statements"""
        return {
            'beginning_balance': self._find_amount_near_keyword(text, ['beginning balance', 'starting balance']),
            'ending_balance': self._find_amount_near_keyword(text, ['ending balance', 'final balance']),
            'large_deposits': self._find_large_amounts(text, threshold=10000)
        }

    def _extract_tax_data(self, text: str) -> Dict:
        """Extract specific data from tax returns"""
        return {
            'agi': self._find_amount_near_keyword(text, ['adjusted gross income', 'agi']),
            'total_income': self._find_amount_near_keyword(text, ['total income', 'wages'])
        }

    def _find_amount_near_keyword(self, text: str, keywords: List[str]) -> Optional[float]:
        """Find monetary amount near specific keywords"""
        for keyword in keywords:
            pattern = rf'{keyword}.*?\$?([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None

    def _find_large_amounts(self, text: str, threshold: float = 10000) -> List[float]:
        """Find amounts above threshold"""
        amounts = self._extract_amounts(text)
        return [amount for amount in amounts if amount >= threshold]

    def process_multiple_documents(self, file_paths: List[str]) -> List[Dict]:
        """Process multiple documents and return results"""
        results = []
        for file_path in file_paths:
            doc_data = self.process_document(file_path)
            if not doc_data.get('error'):
                doc_data['key_data'] = self.extract_key_data(doc_data)
            results.append(doc_data)
        return results