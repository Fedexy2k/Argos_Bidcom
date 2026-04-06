import fitz  # PyMuPDF
from thefuzz import fuzz
from datetime import datetime
import re
import os

class CertAuditor:
    def __init__(self):
        self.validation_results = {
            "critical": [],  # High priority failures (Hard Validations)
            "warnings": [],  # Soft failures (fuzzy match, minor issues)
            "info": []       # General information
        }
        self.status = "PENDING"  # OK, WARNING, FAIL

    def load_pdf(self, pdf_path):
        """Extracts text from a PDF file. Returns text content."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            # Fallback placeholder for OCR
            print(f"Error reading PDF (possible image-only): {e}")
            return ""

    def _normalize_text(self, text):
        """Simple text normalization (lowercase, trip lines)."""
        return " ".join(text.lower().split())

    def _validate_hard(self, audit_text, target_value, field_name):
        """Exact match validation (Critical)."""
        if not target_value:
             return # Skip empty checks

        normalized_audit = self._normalize_text(audit_text)
        normalized_target = self._normalize_text(str(target_value))

        if normalized_target not in normalized_audit:
            self.validation_results["critical"].append(
                f"FAIL: {field_name} mismatch. Expected '{target_value}' not found in cert."
            )
            return False
        return True

    def _validate_model_list(self, audit_text, model_list):
        """Exact match for a list of models."""
        missing_models = []
        normalized_audit = self._normalize_text(audit_text)
        
        for model in model_list:
            if self._normalize_text(model) not in normalized_audit:
                missing_models.append(model)
        
        if missing_models:
            self.validation_results["critical"].append(
                f"FAIL: Missing Models: {', '.join(missing_models)}"
            )
            return False
        return True

    def _validate_soft(self, audit_text, target_value, field_name, threshold=85):
        """
        Fuzzy match validation (Flexible).
        Supports both string and list inputs.
        For lists: checks if ANY item matches above threshold.
        """
        if not target_value:
            return True

        # Convert to list if string
        values_to_check = target_value if isinstance(target_value, list) else [target_value]
        
        normalized_audit = self._normalize_text(audit_text)
        best_ratio = 0
        best_match = None
        
        for val in values_to_check:
            ratio = fuzz.partial_ratio(self._normalize_text(str(val)), normalized_audit)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = val
        
        if best_ratio < threshold:
            self.validation_results["warnings"].append(
                f"WARNING: {field_name} fuzzy match low ({best_ratio}%). Best match: '{best_match}'"
            )
            return False
        return True

    def _check_dates(self, audit_text):
        """
        Validates issuance/expiration dates.
        Logic: Issue date < today and Issue date > (today - 12 months) ? 
        (User requirement: 'Fecha de Emisión: Debe ser menor a la fecha actual y mayor a -12 meses')
        """
        # Regex to find dates is tricky without specific format. Assuming common formats DD/MM/YYYY or YYYY-MM-DD
        # This is a placeholder logic as date extraction is complex without fixed position.
        # We will look for "Fecha de Emisión" or "Fecha:" pattern.
        
        # date_pattern = r"(\d{2}[/-]\d{2}[/-]\d{4})" 
        # dates_found = re.findall(date_pattern, audit_text)
        pass # To be implemented with better regex based on real docs

    def audit(self, pdf_path, json_data):
        """
        Main method to run the audit.
        json_data: The normalized JSON from Module 1.
        """
        self.validation_results = {"critical": [], "warnings": [], "info": []} # Reset
        text = self.load_pdf(pdf_path)

        if not text:
            self.validation_results["critical"].append("FAIL: No text extracted from PDF (OCR needed?).")
            self.status = "FAIL"
            return self.get_report()

        # 1. Hard Validations
        # Titular (Not in JSON example, assuming generic or fixed for user context? 
        # User said: "Titular: -> Buscar 'BIDCOM S.R.L'")
        self._validate_hard(text, "BIDCOM S.R.L", "Titular")
        
        # Marca
        self._validate_hard(text, json_data.get("marca"), "Marca")
        
        # Modelos
        self._validate_model_list(text, json_data.get("modelos_solicitados", []))

        # 2. Soft Validations
        # Fabrica / Direccion
        self._validate_soft(text, json_data.get("fabrica"), "Fábrica")
        self._validate_soft(text, json_data.get("direccion_fabrica"), "Dirección Fábrica")
        
        # Specs (con umbral más bajo porque el formato varía entre documentos)
        self._validate_soft(text, json_data.get("specs_tecnicas"), "Specs Tecnicas", threshold=70)

        # 3. Logic Validations
        self._check_dates(text)

        # Determine Final Status
        if self.validation_results["critical"]:
            self.status = "FAIL"
        elif self.validation_results["warnings"]:
            self.status = "WARNING"
        else:
            self.status = "OK"

        return self.get_report()

    def get_report(self):
        return {
            "status": self.status,
            "details": self.validation_results
        }
