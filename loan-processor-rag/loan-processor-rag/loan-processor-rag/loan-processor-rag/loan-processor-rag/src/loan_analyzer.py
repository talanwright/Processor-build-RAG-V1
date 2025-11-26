from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime, timedelta
from .document_processor import DocumentProcessor
from .vector_database import VectorDatabase

class LoanAnalyzer:
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
        self.document_processor = DocumentProcessor()

        # Required documents by loan type
        self.required_docs = {
            'conventional': [
                'application', 'pay_stub', 'tax_return', 'bank_statement',
                'employment_verification', 'asset_verification', 'appraisal', 'title_report'
            ],
            'fha': [
                'application', 'pay_stub', 'tax_return', 'bank_statement',
                'employment_verification', 'asset_verification', 'appraisal', 'title_report'
            ],
            'va': [
                'application', 'pay_stub', 'tax_return', 'bank_statement',
                'employment_verification', 'certificate_of_eligibility', 'appraisal', 'title_report'
            ]
        }

        # Red flag thresholds
        self.red_flag_thresholds = {
            'large_deposit': 10000,
            'income_variance': 0.10,  # 10% variance threshold
            'employment_gap_days': 30,
            'credit_score_drop': 20
        }

    def analyze_loan_file(self, loan_data: Dict) -> Dict:
        """Main analysis function - analyzes complete loan file"""
        loan_id = loan_data.get('loan_id', 'unknown')
        loan_type = loan_data.get('loan_type', 'conventional').lower()
        documents = loan_data.get('documents', [])

        # Process all documents
        processed_docs = []
        for doc in documents:
            if 'file_path' in doc:
                processed_doc = self.document_processor.process_document(doc['file_path'])
                processed_doc.update(doc)  # Add any additional metadata
                processed_docs.append(processed_doc)

        # Perform analysis
        analysis_result = {
            'loan_id': loan_id,
            'loan_type': loan_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'documents_processed': len(processed_docs),
            'completeness_analysis': self._analyze_completeness(processed_docs, loan_type),
            'red_flag_analysis': self._analyze_red_flags(processed_docs),
            'compliance_check': self._check_compliance(processed_docs),
            'missing_documents': self._identify_missing_documents(processed_docs, loan_type),
            'suggested_actions': [],
            'completeness_score': 0.0,
            'risk_score': 0.0
        }

        # Calculate scores and generate suggestions
        analysis_result['completeness_score'] = self._calculate_completeness_score(analysis_result)
        analysis_result['risk_score'] = self._calculate_risk_score(analysis_result)
        analysis_result['suggested_actions'] = self._generate_suggested_actions(analysis_result)

        return analysis_result

    def _analyze_completeness(self, documents: List[Dict], loan_type: str) -> Dict:
        """Analyze document completeness"""
        required = set(self.required_docs.get(loan_type, self.required_docs['conventional']))
        present = set([doc.get('type', 'unknown') for doc in documents if doc.get('type') != 'unknown'])

        missing = required - present
        extra = present - required

        return {
            'required_documents': list(required),
            'present_documents': list(present),
            'missing_documents': list(missing),
            'extra_documents': list(extra),
            'completion_percentage': (len(present & required) / len(required)) * 100
        }

    def _analyze_red_flags(self, documents: List[Dict]) -> Dict:
        """Analyze documents for red flags"""
        red_flags = []

        for doc in documents:
            doc_type = doc.get('type', 'unknown')
            key_data = doc.get('key_data', {})

            # Income-related red flags
            if doc_type == 'pay_stub':
                red_flags.extend(self._check_paystub_red_flags(doc, key_data))
            elif doc_type == 'bank_statement':
                red_flags.extend(self._check_bank_statement_red_flags(doc, key_data))
            elif doc_type == 'tax_return':
                red_flags.extend(self._check_tax_return_red_flags(doc, key_data))

            # General document red flags
            red_flags.extend(self._check_general_document_red_flags(doc))

        # Cross-document red flags
        red_flags.extend(self._check_cross_document_red_flags(documents))

        return {
            'red_flags_found': len(red_flags),
            'red_flags': red_flags,
            'severity_breakdown': self._categorize_red_flags_by_severity(red_flags)
        }

    def _check_paystub_red_flags(self, doc: Dict, key_data: Dict) -> List[Dict]:
        """Check pay stub specific red flags"""
        red_flags = []
        text = doc.get('text', '').lower()

        # Check for round numbers (potential fraud indicator)
        amounts = key_data.get('amounts', [])
        for amount in amounts:
            if amount > 1000 and amount % 100 == 0:
                red_flags.append({
                    'type': 'round_number_income',
                    'severity': 'medium',
                    'description': f'Round number found in pay stub: ${amount}',
                    'document': doc.get('file_name', 'unknown')
                })

        # Check for missing withholdings
        if 'federal' not in text and 'withholding' not in text:
            red_flags.append({
                'type': 'missing_withholdings',
                'severity': 'high',
                'description': 'Pay stub appears to be missing tax withholdings',
                'document': doc.get('file_name', 'unknown')
            })

        return red_flags

    def _check_bank_statement_red_flags(self, doc: Dict, key_data: Dict) -> List[Dict]:
        """Check bank statement specific red flags"""
        red_flags = []

        # Check for large deposits
        large_deposits = key_data.get('large_deposits', [])
        for deposit in large_deposits:
            red_flags.append({
                'type': 'large_deposit',
                'severity': 'high',
                'description': f'Large deposit requiring explanation: ${deposit:,.2f}',
                'document': doc.get('file_name', 'unknown'),
                'amount': deposit
            })

        return red_flags

    def _check_tax_return_red_flags(self, doc: Dict, key_data: Dict) -> List[Dict]:
        """Check tax return specific red flags"""
        red_flags = []
        text = doc.get('text', '').lower()

        # Check for losses reported
        if 'loss' in text and ('schedule c' in text or 'business' in text):
            red_flags.append({
                'type': 'business_loss',
                'severity': 'medium',
                'description': 'Business loss reported on tax return',
                'document': doc.get('file_name', 'unknown')
            })

        return red_flags

    def _check_general_document_red_flags(self, doc: Dict) -> List[Dict]:
        """Check general document red flags"""
        red_flags = []
        text = doc.get('text', '')

        # Check for poor quality or potential alterations
        if len(text) < 100 and doc.get('type') != 'unknown':
            red_flags.append({
                'type': 'poor_document_quality',
                'severity': 'medium',
                'description': 'Document appears to have poor text extraction quality',
                'document': doc.get('file_name', 'unknown')
            })

        return red_flags

    def _check_cross_document_red_flags(self, documents: List[Dict]) -> List[Dict]:
        """Check for red flags across multiple documents"""
        red_flags = []

        # Find pay stubs and tax returns
        pay_stubs = [doc for doc in documents if doc.get('type') == 'pay_stub']
        tax_returns = [doc for doc in documents if doc.get('type') == 'tax_return']

        # Check income consistency
        if pay_stubs and tax_returns:
            red_flags.extend(self._check_income_consistency(pay_stubs, tax_returns))

        return red_flags

    def _check_income_consistency(self, pay_stubs: List[Dict], tax_returns: List[Dict]) -> List[Dict]:
        """Check income consistency between pay stubs and tax returns"""
        red_flags = []

        # This is a simplified check - in practice you'd need more sophisticated income calculations
        for pay_stub in pay_stubs:
            gross_pay = pay_stub.get('key_data', {}).get('gross_pay')
            if gross_pay:
                # Estimate annual income
                estimated_annual = gross_pay * 26  # Assuming bi-weekly pay

                for tax_return in tax_returns:
                    agi = tax_return.get('key_data', {}).get('agi')
                    if agi:
                        variance = abs(estimated_annual - agi) / agi if agi > 0 else 1
                        if variance > self.red_flag_thresholds['income_variance']:
                            red_flags.append({
                                'type': 'income_discrepancy',
                                'severity': 'high',
                                'description': f'Income discrepancy between pay stub and tax return: {variance:.2%}',
                                'documents': [pay_stub.get('file_name'), tax_return.get('file_name')]
                            })

        return red_flags

    def _categorize_red_flags_by_severity(self, red_flags: List[Dict]) -> Dict:
        """Categorize red flags by severity"""
        severity_count = {'low': 0, 'medium': 0, 'high': 0}
        for flag in red_flags:
            severity = flag.get('severity', 'medium')
            severity_count[severity] += 1
        return severity_count

    def _check_compliance(self, documents: List[Dict]) -> Dict:
        """Check compliance requirements"""
        compliance_issues = []

        # Check for required GLBA protections
        has_ssn = any('ssn' in doc.get('key_data', {}) and doc['key_data']['ssn']
                     for doc in documents)

        if has_ssn:
            compliance_issues.append({
                'type': 'ssn_present',
                'severity': 'high',
                'description': 'SSN detected - ensure GLBA compliance',
                'action_required': 'Implement encryption and access controls'
            })

        return {
            'compliance_issues': compliance_issues,
            'glba_compliant': len(compliance_issues) == 0
        }

    def _identify_missing_documents(self, documents: List[Dict], loan_type: str) -> List[Dict]:
        """Identify missing documents with details"""
        required = set(self.required_docs.get(loan_type, self.required_docs['conventional']))
        present = set([doc.get('type', 'unknown') for doc in documents if doc.get('type') != 'unknown'])

        missing = required - present

        missing_details = []
        for doc_type in missing:
            # Query knowledge base for document requirements
            search_results = self.vector_db.search_requirements(f"{doc_type} requirements")

            description = "Required document"
            if search_results:
                description = search_results[0].get('content', description)[:200] + "..."

            missing_details.append({
                'document_type': doc_type,
                'description': description,
                'urgency': self._get_document_urgency(doc_type),
                'suggested_source': self._get_document_source(doc_type)
            })

        return missing_details

    def _get_document_urgency(self, doc_type: str) -> str:
        """Get urgency level for missing document"""
        high_urgency = ['application', 'pay_stub', 'bank_statement']
        medium_urgency = ['tax_return', 'employment_verification']

        if doc_type in high_urgency:
            return 'high'
        elif doc_type in medium_urgency:
            return 'medium'
        else:
            return 'low'

    def _get_document_source(self, doc_type: str) -> str:
        """Get suggested source for document"""
        sources = {
            'pay_stub': 'Borrower employer',
            'bank_statement': 'Borrower bank',
            'tax_return': 'Borrower or tax preparer',
            'employment_verification': 'Borrower employer HR department',
            'appraisal': 'Licensed appraiser',
            'title_report': 'Title company'
        }
        return sources.get(doc_type, 'Borrower')

    def _calculate_completeness_score(self, analysis: Dict) -> float:
        """Calculate overall completeness score"""
        completeness = analysis.get('completeness_analysis', {})
        return completeness.get('completion_percentage', 0.0) / 100.0

    def _calculate_risk_score(self, analysis: Dict) -> float:
        """Calculate overall risk score based on red flags"""
        red_flags = analysis.get('red_flag_analysis', {})
        severity_breakdown = red_flags.get('severity_breakdown', {})

        # Weight red flags by severity
        risk_score = (
            severity_breakdown.get('low', 0) * 0.1 +
            severity_breakdown.get('medium', 0) * 0.3 +
            severity_breakdown.get('high', 0) * 0.6
        )

        # Normalize to 0-1 scale (max expected red flags: 10)
        return min(risk_score / 10.0, 1.0)

    def _generate_suggested_actions(self, analysis: Dict) -> List[str]:
        """Generate suggested actions based on analysis"""
        actions = []

        # Missing documents
        missing_docs = analysis.get('missing_documents', [])
        if missing_docs:
            high_priority = [doc for doc in missing_docs if doc.get('urgency') == 'high']
            if high_priority:
                actions.append(f"Request high-priority documents: {', '.join([doc['document_type'] for doc in high_priority])}")

        # Red flags
        red_flags = analysis.get('red_flag_analysis', {})
        high_severity_flags = red_flags.get('severity_breakdown', {}).get('high', 0)
        if high_severity_flags > 0:
            actions.append(f"Address {high_severity_flags} high-severity red flags before proceeding")

        # Compliance
        compliance = analysis.get('compliance_check', {})
        if not compliance.get('glba_compliant', True):
            actions.append("Ensure GLBA compliance before processing further")

        # General recommendations
        completeness_score = analysis.get('completeness_score', 0)
        if completeness_score < 0.8:
            actions.append("File is incomplete - request missing documentation")
        elif completeness_score >= 0.9 and analysis.get('risk_score', 1) < 0.3:
            actions.append("File appears ready for underwriting submission")

        return actions