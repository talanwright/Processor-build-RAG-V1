#!/usr/bin/env python3
"""
Document Extractor - Secure Income & Red Flag Detection
Extracts income and identifies red flags while protecting PII
"""

import re
from typing import Dict, List, Any, Optional
from PyPDF2 import PdfReader
import os


class DocumentExtractor:
    """Securely extract income and red flags from loan documents"""

    def __init__(self):
        # Income keywords to search for
        self.income_keywords = [
            'gross pay', 'gross income', 'gross wages',
            'salary', 'wages', 'total income',
            'annual income', 'monthly income',
            'gross earnings', 'ytd gross'
        ]

        # Red flag patterns
        self.red_flag_patterns = {
            'large_deposit': r'\+?\$?\s*([5-9]\d{3,}|[1-9]\d{4,})',  # $5,000+
            'employment_gap': r'(terminated|laid off|unemployed|gap)',
            'address_mismatch': r'(previous address|former address|moved)',
            'recent_job': r'(start date|hire date).*?(202[3-5])',
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file (IN MEMORY ONLY - never saved)

        Security: Text is only in RAM for duration of this function
        """
        try:
            reader = PdfReader(file_path)
            text = ""

            for page in reader.pages:
                text += page.extract_text() + "\n"

            return text

        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    def sanitize_for_logging(self, text: str) -> str:
        """
        Aggressively redact PII from any text before logging
        """
        # Redact SSN
        text = re.sub(r'\d{3}-\d{2}-\d{4}', 'XXX-XX-XXXX', text)
        text = re.sub(r'\b\d{9}\b', 'XXXXXXXXX', text)

        # Redact account numbers
        text = re.sub(r'\b\d{10,16}\b', 'XXXX-XXXX-XXXX', text)

        # Redact credit card numbers
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX', text)

        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'user@email.com', text)

        # Redact phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'XXX-XXX-XXXX', text)

        return text

    def extract_income_amounts(self, text: str) -> List[float]:
        """
        Find all dollar amounts that appear near income keywords

        Returns: List of income amounts (NO PII, just numbers)
        """
        income_amounts = []
        lines = text.lower().split('\n')

        for i, line in enumerate(lines):
            # Check if line contains income keywords
            if any(keyword in line for keyword in self.income_keywords):
                # Look in current line and next 2 lines for dollar amounts
                search_text = ' '.join(lines[i:i+3])

                # Find dollar amounts: $5,000.00 or 5000.00 or 5,000
                amounts = re.findall(r'\$?\s*([\d,]+\.?\d{0,2})', search_text)

                for amount_str in amounts:
                    try:
                        # Remove commas and convert to float
                        amount = float(amount_str.replace(',', ''))

                        # Only consider reasonable income amounts ($100 - $1,000,000/month)
                        if 100 <= amount <= 1000000:
                            income_amounts.append(amount)
                    except ValueError:
                        continue

        return income_amounts

    def calculate_monthly_income(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Calculate total monthly income from document

        Returns: {
            "amount": 8500.00,
            "source": "pay_stub",
            "confidence": "high"
        }
        """
        filename_lower = filename.lower()
        income_amounts = self.extract_income_amounts(text)

        if not income_amounts:
            return {
                "amount": 0.0,
                "source": "unknown",
                "confidence": "none"
            }

        # Determine document type from filename
        doc_type = "unknown"
        is_annual = False

        if any(kw in filename_lower for kw in ['paystub', 'pay_stub', 'payslip', 'pay slip']):
            doc_type = "pay_stub"
            # Pay stubs are usually bi-weekly or monthly

        elif any(kw in filename_lower for kw in ['w2', 'w-2', 'wage']):
            doc_type = "w2"
            is_annual = True

        elif any(kw in filename_lower for kw in ['1040', 'tax', 'return']):
            doc_type = "tax_return"
            is_annual = True

        # Get the largest amount (usually the gross income)
        max_amount = max(income_amounts)

        # Convert to monthly if annual
        if is_annual:
            monthly_amount = max_amount / 12
        else:
            # Assume pay stub is bi-weekly (most common)
            if doc_type == "pay_stub":
                # Check if "bi-weekly" or "semi-monthly" in text
                if 'bi-weekly' in text.lower() or 'biweekly' in text.lower():
                    monthly_amount = max_amount * 26 / 12  # 26 pay periods per year
                elif 'weekly' in text.lower():
                    monthly_amount = max_amount * 52 / 12  # 52 weeks per year
                else:
                    # Assume monthly
                    monthly_amount = max_amount
            else:
                monthly_amount = max_amount

        # Determine confidence
        confidence = "high" if len(income_amounts) >= 2 else "medium" if len(income_amounts) == 1 else "low"

        return {
            "amount": round(monthly_amount, 2),
            "source": doc_type,
            "confidence": confidence
        }

    def detect_red_flags(self, text: str, income_data: List[Dict]) -> List[Dict[str, str]]:
        """
        Detect potential red flags in documents

        Returns: List of red flags (NO PII - generic descriptions only)
        """
        red_flags = []
        text_lower = text.lower()

        # 1. Income Inconsistency
        if len(income_data) >= 2:
            amounts = [item['amount'] for item in income_data]
            max_income = max(amounts)
            min_income = min(amounts)

            # If incomes differ by more than 20%
            if max_income > 0 and (max_income - min_income) / max_income > 0.20:
                red_flags.append({
                    "type": "income_inconsistency",
                    "severity": "medium",
                    "description": f"Income amounts vary significantly across documents (${min_income:,.0f} - ${max_income:,.0f})",
                    "recommendation": "Request explanation for income variance"
                })

        # 2. Large Deposit Detection
        large_deposits = re.findall(r'deposit.*?\$?\s*([\d,]+\.?\d{0,2})', text_lower)
        for deposit_str in large_deposits:
            try:
                deposit = float(deposit_str.replace(',', ''))
                if deposit >= 5000:
                    red_flags.append({
                        "type": "large_deposit",
                        "severity": "medium",
                        "description": f"Large deposit detected (${deposit:,.0f}) - may need source verification",
                        "recommendation": "Request gift letter or source documentation"
                    })
            except ValueError:
                pass

        # 3. Employment Gap
        if re.search(self.red_flag_patterns['employment_gap'], text_lower):
            red_flags.append({
                "type": "employment_gap",
                "severity": "low",
                "description": "Possible employment gap or job change detected",
                "recommendation": "Verify continuous employment history"
            })

        # 4. Recent Job Change
        if re.search(self.red_flag_patterns['recent_job'], text):
            red_flags.append({
                "type": "recent_employment",
                "severity": "medium",
                "description": "Recent job start date detected (within last 2 years)",
                "recommendation": "Verify employment stability and probation period"
            })

        # 5. Address Mismatch
        if re.search(self.red_flag_patterns['address_mismatch'], text_lower):
            red_flags.append({
                "type": "address_change",
                "severity": "low",
                "description": "Multiple addresses detected in documentation",
                "recommendation": "Verify current residence and occupancy intent"
            })

        # 6. Document Age (if we can detect dates)
        current_year = 2025
        years_found = re.findall(r'\b(20\d{2})\b', text)
        if years_found:
            oldest_year = min([int(y) for y in years_found])
            if current_year - oldest_year > 1:
                red_flags.append({
                    "type": "outdated_documents",
                    "severity": "medium",
                    "description": f"Document contains dates from {oldest_year} - may be outdated",
                    "recommendation": "Request current documentation (within 60 days)"
                })

        # 7. High DTI Indicator
        debt_keywords = ['loan', 'credit card', 'auto payment', 'student loan', 'mortgage']
        debt_count = sum(1 for keyword in debt_keywords if keyword in text_lower)
        if debt_count >= 3:
            red_flags.append({
                "type": "multiple_debts",
                "severity": "medium",
                "description": f"Multiple debt obligations detected ({debt_count} types)",
                "recommendation": "Calculate DTI ratio carefully"
            })

        # Remove duplicates based on type
        seen_types = set()
        unique_flags = []
        for flag in red_flags:
            if flag['type'] not in seen_types:
                seen_types.add(flag['type'])
                unique_flags.append(flag)

        return unique_flags

    def analyze_documents(self, loan_dir: str, documents: List[Dict]) -> Dict[str, Any]:
        """
        Main analysis function - extracts income and red flags from all documents

        Security: All text extraction happens in memory, nothing is saved

        Returns: {
            "total_monthly_income": 8500.00,
            "income_breakdown": [...],
            "red_flags": [...],
            "confidence": "high"
        }
        """
        income_breakdown = []
        all_red_flags = []
        all_text = ""  # Combine all text for cross-document analysis

        # Process each document
        for doc in documents:
            filename = doc.get('filename', '')
            file_path = os.path.join(loan_dir, filename)

            if not os.path.exists(file_path):
                continue

            # Only process PDFs (skip images for now)
            if not filename.lower().endswith('.pdf'):
                continue

            # Extract text (IN MEMORY ONLY)
            text = self.extract_text_from_pdf(file_path)

            if not text:
                continue

            # Combine for cross-document analysis
            all_text += text + "\n"

            # Extract income from this document
            income_data = self.calculate_monthly_income(text, filename)

            if income_data['amount'] > 0:
                income_breakdown.append({
                    "document": filename,
                    "monthly_amount": income_data['amount'],
                    "source": income_data['source'],
                    "confidence": income_data['confidence']
                })

            # CRITICAL: Delete text from memory immediately after processing
            del text

        # Detect red flags across all documents
        all_red_flags = self.detect_red_flags(all_text, income_breakdown)

        # CRITICAL: Delete combined text from memory
        del all_text

        # Calculate total monthly income
        total_income = sum(item['monthly_amount'] for item in income_breakdown)

        # Determine overall confidence
        if len(income_breakdown) >= 2:
            overall_confidence = "high"
        elif len(income_breakdown) == 1:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"

        return {
            "total_monthly_income": round(total_income, 2),
            "income_breakdown": income_breakdown,
            "red_flags": all_red_flags,
            "red_flag_count": len(all_red_flags),
            "confidence": overall_confidence,
            "documents_analyzed": len([d for d in documents if d.get('filename', '').lower().endswith('.pdf')])
        }


# Singleton instance
extractor = DocumentExtractor()
