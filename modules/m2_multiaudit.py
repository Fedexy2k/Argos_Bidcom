from modules.m2_strategies import StrategyFactory
from modules.m2_audit import CertAuditor
import os

class MultiCertAuditor(CertAuditor):
    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger
    
    def _log(self, level, message):
        """Helper para logging condicional"""
        if self.logger:
            if level == "DEBUG":
                self.logger.debug(message)
            elif level == "INFO":
                self.logger.info(message)
            elif level == "WARN":
                self.logger.warning(message)
            elif level == "ERROR":
                self.logger.error(message)

    def audit_multiple(self, json_data, pdf_paths_dict):
        # ... (setup consolidated_report)
        self._log("INFO", "")
        self._log("INFO", "╔══════════════════════════════════════════╗")
        self._log("INFO", "║  INICIANDO AUDITORÍA MULTICERTIFICADO   ║")
        self._log("INFO", "╚══════════════════════════════════════════╝")
        self._log("INFO", "")
        
        from typing import Any
        consolidated_report: dict[str, Any] = {
            "status": "OK",
            "details": {} 
        }

        req_certs = json_data.get("certificados_requeridos", [])
        
        self._log("INFO", f"Certificados requeridos: {len(req_certs)}")
        for i, req in enumerate(req_certs, 1):
            self._log("INFO", f"  {i}. {req['tipo']}")
        self._log("INFO", "")
        
        for req in req_certs:
            cert_type = req["tipo"]
            pdf_path = pdf_paths_dict.get(cert_type)
            report_key = f"CERT_{cert_type}"
            
            self._log("INFO", "─" * 60)
            self._log("INFO", f"PROCESANDO: {cert_type}")
            self._log("INFO", "─" * 60)
            
            if not pdf_path or not os.path.exists(pdf_path):
                self._log("ERROR", f"❌ Archivo PDF no encontrado para {cert_type}")
                self._log("DEBUG", f"  Path esperado: {pdf_path}")
                
                consolidated_report["details"][report_key] = {
                    "status": "FAIL",
                    "details": {"critical": [f"Archivo PDF no encontrado para {cert_type}"], "warnings": [], "info": []},
                    "metadata": {}
                }
                consolidated_report["status"] = "FAIL"
                continue

            self._log("INFO", f"📄 PDF: {os.path.basename(pdf_path)}")
            self._log("DEBUG", f"  Path completo: {pdf_path}")
            
            # Resetear estado interno
            self.validation_results = {"critical": [], "warnings": [], "info": []}
            self.status = "PENDING"
            
            self._log("DEBUG", "Extrayendo texto del PDF...")
            text = self.load_pdf(pdf_path)
            
            if not text:
                self._log("ERROR", "❌ No se pudo extraer texto del PDF")
                self.validation_results["critical"].append("FAIL: No text extracted from PDF.")
                self.status = "FAIL"
            else:
                self._log("INFO", f"✓ Texto extraído: {len(text)} caracteres")
                self._log("DEBUG", f"  Primeros 200 caracteres: {text[:200]}...")
                
                # --- STRATEGY PATTERN ---
                # 1. Detectar Estrategia (LenorToy, Standard, etc)
                product_type = json_data.get("tipo_producto", "UNKNOWN")
                self._log("DEBUG", f"Tipo de producto: {product_type}")
                
                # Pasamos 'self.validation_results' para que la estrategia escriba ahí
                strategy = StrategyFactory.get_strategy(text, product_type, self.validation_results, self.logger)
                
                # 2. Ejecutar validación delegada
                self._log("INFO", "")
                strategy.validate(text, json_data, cert_type)
                self._log("INFO", "")

                # --- FIN STRATEGY PATTERN ---

                # Determinar estado individual
                if self.validation_results["critical"]:
                    self.status = "FAIL"
                    self._log("ERROR", f"Estado: FAIL ({len(self.validation_results['critical'])} errores críticos)")
                elif self.validation_results["warnings"]:
                    self.status = "WARNING"
                    self._log("WARN", f"Estado: WARNING ({len(self.validation_results['warnings'])} advertencias)")
                else:
                    self.status = "OK"
                    self._log("INFO", "Estado: ✓ OK - Validación exitosa")

            # Agregar al reporte consolidado
            report = self.get_report()
            
            # Agregar metadata de validación si existe
            if hasattr(strategy, 'validation_metadata'):
                report["metadata"] = strategy.validation_metadata
            else:
                report["metadata"] = {}
            
            consolidated_report["details"][report_key] = report
            
            # Actualizar estado global
            if self.status == "FAIL":
                consolidated_report["status"] = "FAIL"
            elif self.status == "WARNING" and consolidated_report["status"] != "FAIL":
                consolidated_report["status"] = "WARNING"
        
        self._log("INFO", "")
        self._log("INFO", "═" * 60)
        self._log("INFO", f"AUDITORÍA COMPLETADA - Estado global: {consolidated_report['status']}")
        self._log("INFO", "═" * 60)
        self._log("INFO", "")

        return consolidated_report
