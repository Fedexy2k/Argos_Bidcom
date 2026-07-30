from thefuzz import fuzz
import sys
import re

class AuditStrategy:
    """Clase base para estrategias de auditoría."""
    def __init__(self, validation_results_ref, logger=None):
        from typing import Any
        self.validation_results = validation_results_ref
        self.logger = logger
        self.validation_metadata: dict[str, Any] = {}  # Para guardar detalles de cada validación

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

    def _normalize_text(self, text):
        return " ".join(text.lower().split())

    def _validate_hard(self, audit_text, target_value, field_name):
        """Exact match validation (Critical). Supports multiple values (split by / or ,)."""
        self._log("DEBUG", f"\n>> Validando campo: {field_name.upper()} (Hard Match)")
        
        if not target_value:
            self._log("DEBUG", f"   Campo '{field_name}' vacío en datasheet - Omitido")
            return True
        
        self._log("DEBUG", f"   Esperado: \"{target_value}\"")
        self._log("DEBUG", f"   Buscando en PDF...")
        
        normalized_audit = self._normalize_text(audit_text)
        
        # Manejar múltiples valores posibles (ej: "GADNIC, MAWE" o "GADNIC / MAWE")
        raw_target = str(target_value)
        targets = [t.strip() for t in raw_target.replace(',', '/').split('/')]
        
        self._log("DEBUG", f"   Valores a buscar: {targets}")
        
        # Verificar si AL MENOS UNA de las marcas está presente
        match_found = False
        found_value = None
        for target in targets:
            normalized_target = self._normalize_text(target)
            if normalized_target in normalized_audit:
                match_found = True
                found_value = target
                break
        
        if not match_found:
            self._log("ERROR", f"   ❌ {field_name}: Ningún valor coincide")
            self._log("DEBUG", f"   Búsquedas intentadas: {len(targets)}")
            for t in targets:
                self._log("DEBUG", f"      - \"{t}\" → No encontrado")
            
            self.validation_results["critical"].append(
                f"FAIL: {field_name} mismatch. Expected one of '{targets}' not found."
            )
            
            # Guardar metadata
            self.validation_metadata[field_name] = {
                "status": "FAIL",
                "expected": target_value,
                "found": None,
                "attempts": targets
            }
            return False
        
        self._log("INFO", f"   ✓ {field_name}: Match encontrado - \"{found_value}\"")
        self.validation_metadata[field_name] = {
            "status": "OK",
            "expected": target_value,
            "found": found_value,
            "match_type": "exact"
        }
        return True

    def _validate_soft(self, audit_text, target_value, field_name, threshold=85):
        """Fuzzy match validation."""
        self._log("DEBUG", f"\n>> Validando campo: {field_name.upper()} (Fuzzy Match, threshold={threshold}%)")
        
        if not target_value:
            self._log("DEBUG", f"   Campo '{field_name}' vacío en datasheet - Omitido")
            return True
        
        target_list = target_value if isinstance(target_value, list) else [target_value]
        self._log("DEBUG", f"   Esperado: {target_list}")
        self._log("DEBUG", f"   Buscando coincidencias fuzzy...")
        
        normalized_audit = self._normalize_text(audit_text)
        
        best_ratio = 0
        best_match = None
        
        for val in target_list:
            ratio = fuzz.partial_ratio(self._normalize_text(str(val)), normalized_audit)
            self._log("DEBUG", f"   - \"{val}\": {ratio}% similitud")
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = val
        
        if best_ratio < threshold:
            self._log("WARN", f"   ⚠️ {field_name}: Match bajo ({best_ratio}% < {threshold}%)")
            self._log("DEBUG", f"   Mejor coincidencia: \"{best_match}\"")
            
            self.validation_results["warnings"].append(
                f"WARNING: {field_name} fuzzy match low ({best_ratio}%). Best match: '{best_match}'"
            )
            
            self.validation_metadata[field_name] = {
                "status": "WARNING",
                "expected": target_value,
                "found": best_match,
                "match_ratio": best_ratio,
                "threshold": threshold
            }
            return False
        
        self._log("INFO", f"   ✓ {field_name}: Match aceptable ({best_ratio}% >= {threshold}%)")
        self.validation_metadata[field_name] = {
            "status": "OK",
            "expected": target_value,
            "found": best_match,
            "match_ratio": best_ratio,
            "match_type": "fuzzy"
        }
        return True

    def _validate_model_list(self, audit_text, model_list):
        """Standard model validation."""
        self._log("DEBUG", f"\n>> Validando MODELOS (Lista completa)")
        self._log("DEBUG", f"   Modelos esperados: {model_list}")
        
        missing_models = []
        found_models = []
        normalized_audit = self._normalize_text(audit_text)
        
        for model in model_list:
            self._log("DEBUG", f"   Buscando modelo: \"{model}\"")
            if self._normalize_text(model) not in normalized_audit:
                self._log("DEBUG", f"      → No encontrado")
                missing_models.append(model)
            else:
                self._log("DEBUG", f"      → ✓ Encontrado")
                found_models.append(model)
        
        if missing_models:
            self._log("ERROR", f"   ❌ MODELOS: Faltan {len(missing_models)} de {len(model_list)}")
            self._log("DEBUG", f"   Faltantes: {missing_models}")
            
            self.validation_results["critical"].append(
                f"FAIL: Missing Models: {', '.join(missing_models)}"
            )
            
            self.validation_metadata["Modelos"] = {
                "status": "FAIL",
                "expected": model_list,
                "found": found_models,
                "missing": missing_models
            }
            return False
        
        self._log("INFO", f"   ✓ MODELOS: Todos encontrados ({len(model_list)} modelos)")
        self.validation_metadata["Modelos"] = {
            "status": "OK",
            "expected": model_list,
            "found": found_models
        }
        return True

    def _validate_specs(self, audit_text, specs_data, field_name="Specs Técnicas"):
        """Valida especificaciones técnicas con lógica híbrida (Texto + Valores Eléctricos)."""
        self._log("DEBUG", f"\n>> Validando campo: {field_name.upper()}")
        
        if not specs_data:
            self._log("DEBUG", f"   Campo '{field_name}' vacío en datasheet - Omitido")
            return True

        # Preprocesamiento inteligente: Dividir bloques de texto en líneas individuales
        specs_list = []
        raw_items = specs_data if isinstance(specs_data, list) else [specs_data]
        
        for item in raw_items:
            if isinstance(item, str) and '\n' in item:
                # Dividir por líneas y limpiar
                lines = [l.strip() for l in item.split('\n') if len(l.strip()) > 3] # Ignorar muy cortas
                specs_list.extend(lines)
            elif item:
                specs_list.append(str(item).strip())
        
        # Eliminar duplicados y campos obvios (Marca, Modelo ya validados aparte)
        specs_list = [s for s in specs_list if not any(x in s.upper() for x in ["MARCA:", "MODELO:"])]
        
        if not specs_list:
             self._log("WARN", "   Specs vacías después de preprocesar")
             return True

        self._log("DEBUG", f"   Specs individuales a buscar: {len(specs_list)}")
        
        normalized_audit = self._normalize_text(audit_text)
        found_specs = []
        missing_specs = []
        
        # Regex para unidades comunes (V, Hz, W, A)
        # Busca número + unidad opcionalmente separada por espacio
        tech_patterns = {
            "V": r'(\d+[.,]?\d*)\s*[Vv](?:olts?)?',
            "Hz": r'(\d+[.,]?\d*)\s*[Hh]z',
            "W": r'(\d+[.,]?\d*)\s*[Ww](?:atts?)?',
            "A": r'(\d+[.,]?\d*)\s*[Aa](?:mps?)?'
        }
        
        for spec in specs_list:
            norm_spec = self._normalize_text(spec)
            
            # 1. Búsqueda exacta normalizada
            if norm_spec in normalized_audit:
                found_specs.append(spec)
                continue
                
            # 2. Fuzzy textual (si el texto es muy similar)
            if len(norm_spec) < 100:
                if fuzz.partial_ratio(norm_spec, normalized_audit) > 85:
                    found_specs.append(f"{spec}")
                    continue

            # 3. Lógica Eléctrica (Regex Numérico) - "Context Match"
            electrical_match = False
            for unit, pattern in tech_patterns.items():
                # Buscar valores en el SPEC actual (datasheet)
                matches_in_spec = re.findall(pattern, spec)
                
                for val in matches_in_spec:
                    # Normalizar valor (reemplazar coma por punto para regex si es necesario, aunque en pdf buscamos literal)
                    val_clean = val.replace(',', '.') 
                    
                    # Buscar VALOR + UNIDAD en el PDF (Tolerante a espacios y case)
                    # Ej: Si spec tiene "220", buscamos "220" seguido de "V" cerca
                    # Simplificación: Buscamos pattern de unidad cerca del valor
                    
                    # Construir regex para buscar en el PDF normalized
                    # normalized_audit ya tiene todo en lowercase sin saltos lineas raros
                    
                    pdf_pattern = rf'{re.escape(val_clean)}\s*{unit.lower()}' 
                    
                    if re.search(pdf_pattern, normalized_audit, re.IGNORECASE):
                        electrical_match = True
                        found_specs.append(f"{spec} (Match {unit}: {val})")
                        break 
                if electrical_match: break
            
            if electrical_match: continue

            # Si falla todo
            missing_specs.append(spec)
        
        # Resultado
        status = "OK"
        if missing_specs:
            # Si encontramos al menos el 40%, es Warning, sino Fail
            if specs_list:
                success_rate = len(found_specs) / len(specs_list)
                status = "WARNING" if success_rate > 0.4 else "FAIL" 
            else:
                status = "FAIL"
            
            self._log("WARN", f"   ⚠️ {field_name}: Encontradas {len(found_specs)}/{len(specs_list)}")
            
            # Detalle explícito de faltantes
            self._log("INFO", "   [DETALLE] Items NO encontrados:")
            for ms in missing_specs:
                 self._log("WARN", f"     [FALTA] {ms}")

            self.validation_results["warnings"].append(
                f"WARNING: Specs incompletas. Encontradas {len(found_specs)}/{len(specs_list)} items."
            )
        else:
            self._log("INFO", f"   ✓ {field_name}: Todas encontradas")
            
        
        # AI Fallback: Si la validación tradicional falla, intentar con IA
        if status in ["FAIL", "WARNING"] and missing_specs:
            self._log("INFO", "   Specs tradicionales fallaron. Intentando validación con IA...")
            try:
                from modules.ai_helper import AISpecsHelper
                
                ai_helper = AISpecsHelper()
                
                # Construir dict de specs esperadas para la IA
                expected_specs = {
                    'full_spec': ', '.join(specs_list),
                    'missing': missing_specs
                }
                
                ai_result = ai_helper.validate_specs_in_text(
                    pdf_text=audit_text,
                    expected_specs=expected_specs,
                    strict=False
                )
                
                # Si IA encontró las specs con alta confianza, actualizar status
                if ai_result.get('found') and ai_result.get('confidence', 0) >= 0.75:
                    self._log("INFO", f"   ✓ IA validó specs (confianza: {ai_result['confidence']:.0%})")
                    self._log("INFO", f"     Razón: {ai_result.get('reasoning', 'N/A')}")
                    
                    # Actualizar status
                    status = "OK"
                    
                    # Actualizar found_specs para que se muestre en la UI
                    found_specs = specs_list.copy()  # Marcar todas como encontradas
                    missing_specs = []  # Ya no hay faltantes
                    
                    # Limpiar warnings previos
                    self.validation_results["warnings"] = [
                        w for w in self.validation_results["warnings"] 
                        if "Specs incompletas" not in w
                    ]
                else:
                    self._log("WARN", f"   IA tampoco validó specs (confianza: {ai_result.get('confidence', 0):.0%})")
                    
            except ImportError:
                self._log("DEBUG", "   AI helper no disponible (pip install google-generativeai)")
            except ValueError as e:
                self._log("DEBUG", f"   API key de Gemini no configurada: {e}")
            except Exception as e:
                self._log("ERROR", f"   Error en validación IA: {e}")
        
        # Crear metadata SIEMPRE al final (después de posible corrección por IA)
        self.validation_metadata[field_name] = {
            "status": status,
            "expected": specs_list, 
            "found": found_specs if found_specs else ["Ninguna encontrada"],
            "missing": missing_specs
        }
        
        # Si IA validó, agregar flag
        if status == "OK" and not missing_specs and len(found_specs) == len(specs_list):
            # Verificar si fue la IA quien aprobó (si antes había faltantes)
            if field_name in self.validation_metadata:
                self.validation_metadata[field_name]["ai_validated"] = True
        
        return status == "OK"

    def validate(self, text, json_data, cert_type):
        """Default validation logic."""
        self._log("INFO", "=== Validación con Estrategia Estándar ===")
        
        # Marca
        self._validate_hard(text, json_data.get("marca"), "Marca")
        
        # Modelos
        self._validate_model_list(text, json_data.get("modelos_solicitados", []))
        
        # Fábrica (Soft)
        if cert_type != "FTALATOS":
             self._validate_soft(text, json_data.get("fabrica"), "Fábrica")
             self._validate_soft(text, json_data.get("direccion_fabrica"), "Dirección Fábrica")

        # Specs Técnicas (Agregado para estrategia estándar/todas)
        self._validate_specs(text, json_data.get("specs_tecnicas"), "Specs Técnicas")


class LenorToyStrategy(AuditStrategy):
    """Reglas específicas para Juguetes certificados por Lenor."""
    
    def validate(self, text, json_data, cert_type):
        
        self._log("INFO", "=== Validación con LENOR TOY STRATEGY ===")
        self._log("INFO", f"Tipo de certificado: {cert_type}")
        
        # Regla 1: Marca es opcional/warning en Ftalatos
        if cert_type == "FTALATOS":
            self._log("DEBUG", "Certificado de Ftalatos detectado - Marca es warning (no critical)")
            normalized_audit = self._normalize_text(text)
            target = json_data.get("marca")
            if target and self._normalize_text(target) not in normalized_audit:
                 self._log("WARN", f"⚠️ Marca '{target}' no encontrada en Ftalatos (común en Lenor/Químicos)")
                 self.validation_results["warnings"].append(
                     f"WARNING: Marca '{target}' no encontrada en Ftalatos (Común en Lenor/Químicos)."
                 )
                 # Guardar metadata aunque sea warning para manual approval
                 self.validation_metadata["Marca"] = {
                     "status": "WARNING",
                     "expected": target,
                     "found": "Not found (Ftalatos)"
                 }
        else:
            self._validate_hard(text, json_data.get("marca"), "Marca")

        # Regla 2: Modelos
        self._validate_model_list(text, json_data.get("modelos_solicitados", []))

        # Regla 3: Fábrica
        if cert_type != "FTALATOS":
             self._validate_soft(text, json_data.get("fabrica"), "Fábrica")
             self._validate_soft(text, json_data.get("direccion_fabrica"), "Dirección Fábrica")
             
        # Regla 4: Specs Técnicas (Nuevo)
        # Intentamos validar specs si existen en el datasheet
        self._validate_specs(text, json_data.get("specs_tecnicas"), "Technical Specs")




class CBSchemeStrategy(AuditStrategy):
    """Reglas específicas para certificados CB Scheme (IEC System - TÜV, SGS, Intertek, BV)."""
    
    def validate(self, text, json_data, cert_type):
        
        self._log("INFO", "=== Validación con CB SCHEME STRATEGY ===")
        self._log("INFO", f"Tipo de certificado: {cert_type}")
        self._log("DEBUG", "CB Scheme: Estructura internacional estandarizada")
        
        # CB Scheme tiene estructura muy estándar y completa
        # Marca: En CB aparece como "Trademark / Brand"
        self._log("DEBUG", "Campo MARCA en CB: Aparece como 'Trademark' o 'Brand'")
        self._validate_hard(text, json_data.get("marca"), "Marca")
        
        # Modelo: En CB aparece como "Model / Type Ref."
        self._log("DEBUG", "Campo MODELO en CB: Aparece como 'Model' o 'Type Reference'")
        self._validate_model_list(text, json_data.get("modelos_solicitados", []))
        
        # Fábrica: CB tiene direcciones muy completas con país
        # Usar soft con threshold relajado porque pueden tener diferencias de formato
        self._log("DEBUG", "Campo FÁBRICA: Threshold relajado (70%) por formato variable")
        self._validate_soft(text, json_data.get("fabrica"), "Fábrica", threshold=70)
        
        # Specs: En CB están en "Ratings" o "Additional information" (página 2)
        # Son muy detalladas, valdría match parcial de voltajes clave
        if json_data.get("specs_tecnicas"):
            self._log("DEBUG", "Validando especificaciones técnicas (voltajes, potencias...)")
            # Para CB, las specs son tan detalladas que hacer match exacto es difícil
            # Extraer valores clave del datasheet (ej: voltajes principales)
            self._validate_specs_cb(text, json_data.get("specs_tecnicas"))
    
    def _validate_specs_cb(self, audit_text, specs_from_datasheet):
        """
        Validación especial para specs de CB.
        Extrae valores numéricos clave (voltajes, frecuencias) y busca coincidencias.
        """
        import re
        
        self._log("DEBUG", "\n>> Validando ESPECIFICACIONES TÉCNICAS (CB Scheme)")
        self._log("DEBUG", f"   Specs desde datasheet: {str(specs_from_datasheet)[:100]}...")
        
        # Extraer números con unidades del datasheet
        # Ej: "220V", "50Hz", "800W", "100A"
        pattern = r'\d+[.,]?\d*\s*[VWAHz~⎓]+'
        
        datasheet_values = set(re.findall(pattern, str(specs_from_datasheet)))
        cert_values = set(re.findall(pattern, audit_text))
        
        self._log("DEBUG", f"   Valores técnicos en datasheet: {datasheet_values}")
        self._log("DEBUG", f"   Valores técnicos en certificado: {len(cert_values)} encontrados")
        
        # Calcular coincidencias
        matches = datasheet_values.intersection(cert_values)
        
        self._log("DEBUG", f"   Coincidencias: {matches}")
        
        if not matches:
            self._log("WARN", "   ⚠️ SPECS: No se encontraron valores técnicos coincidentes")
            self.validation_results["warnings"].append(
                f"WARNING: Specs Técnicas - No se encontraron valores coincidentes específicos (voltajes/potencias)."
            )
        elif len(matches) < len(datasheet_values) * 0.5:  # Menos del 50% match
            self._log("WARN", f"   ⚠️ SPECS: Match parcial ({len(matches)}/{len(datasheet_values)} valores)")
            self.validation_results["warnings"].append(
                f"WARNING: Specs Técnicas - Match parcial ({len(matches)}/{len(datasheet_values)} valores coinciden)."
            )
        else:
            self._log("INFO", f"   ✓ SPECS: Match aceptable ({len(matches)}/{len(datasheet_values)} valores)")


class QetkraStrategy(AuditStrategy):
    """Reglas específicas para certificados de Qetkra (certificadora argentina)."""
    
    def validate(self, text, json_data, cert_type):
        
        self._log("INFO", "=== Validación con QETKRA STRATEGY ===")
        self._log("INFO", f"Tipo de certificado: {cert_type}")
        self._log("DEBUG", "Qetkra: Certificadora nacional argentina (ISO/IEC 17067 Sistema Nº 2)")
        
        # Qetkra es muy similar a la estrategia estándar pero con algunas particularidades
        
        # 1. Marca (Hard match)
        self._log("DEBUG", "Campo MARCA: Aparece como 'Trademark' o directamente en sección")
        self._validate_hard(text, json_data.get("marca"), "Marca")
        
        # 2. Modelos (Lista completa)
        self._log("DEBUG", "Campo MODELOS: Pueden aparecer en 'Model or type' o tabla separada")
        self._validate_model_list(text, json_data.get("modelos_solicitados", []))
        
        # 3. Fábrica (Soft match con threshold estándar 85%)
        # Quektra incluye nombre completo y dirección bien detallados
        self._log("DEBUG", "Campo FÁBRICA: Nombre completo del fabricante")
        self._validate_soft(text, json_data.get("fabrica"), "Fábrica", threshold=85)
        
        # 4. Dirección (Soft match con threshold 85%)
        self._log("DEBUG", "Campo DIRECCIÓN: Dirección completa con provincia/país")
        self._validate_soft(text, json_data.get("direccion_fabrica"), "Dirección Fábrica", threshold=85)
        
        # 5. Specs Técnicas
        # Quektra incluye specs en 'Características técnicas' o similar
        if json_data.get("specs_tecnicas"):
            self._log("DEBUG", "Validando especificaciones técnicas (voltajes, corrientes, potencias...)")
            self._validate_specs(text, json_data.get("specs_tecnicas"), "Specs Técnicas")


class StrategyFactory:
    @staticmethod
    def get_strategy(text_content, product_type, base_results, logger=None):
        """
        Retorna la estrategia adecuada detectando keywords en el texto.
        Prioridad: CB Scheme > Quektra > Lenor > Default
        """
        text_lower = text_content.lower()
        
        if logger:
            logger.debug("\n=== DETECCIÓN DE ESTRATEGIA DE VALIDACIÓN ===")
            logger.debug(f"Tipo de producto: {product_type}")
            logger.debug("Analizando contenido del certificado...")
        
        # 1. Detectar CB Scheme (internacional)
        is_cb = "cb scheme" in text_lower or "iecee" in text_lower or "cb test certificate" in text_lower
        
        if is_cb:
            if logger:
                logger.info("✓ Estrategia detectada: CB SCHEME")
                logger.debug("Keywords encontradas: CB Scheme / IECEE")
            return CBSchemeStrategy(base_results, logger)
        
        # 2. Detectar Quektra (certificadora nacional argentina)
        is_quektra = ("q-ar-" in text_lower or 
                      "iso/iec 17067" in text_lower or
                      "conformidad de tipo" in text_lower and "q-ar" in text_lower)
        
        if is_quektra:
            if logger:
                logger.info("✓ Estrategia detectada: QETKRA")
                logger.debug("Keywords encontradas: Q-AR- / ISO/IEC 17067 / Conformidad de Tipo")
            return QetkraStrategy(base_results, logger)
        
        # 3. Detectar OEC Nacional (Lenor, IRAM, etc.)
        is_lenor = "lenor" in text_lower
        is_iram = "iram" in text_lower and "instituto argentino" in text_lower
        is_toy = product_type == "JUGUETES"
        
        if is_lenor and is_toy:
            if logger:
                logger.info("✓ Estrategia detectada: LENOR TOY")
                logger.debug("Keywords: Lenor + Producto tipo JUGUETES")
            return LenorToyStrategy(base_results, logger)
            
        if is_iram:
            if logger:
                logger.info("✓ Estrategia detectada: IRAM (Estándar)")
                logger.debug("Keywords: IRAM / Instituto Argentino de Normalización")
            return AuditStrategy(base_results, logger)
        
        # 4. Default (validación estándar)
        if logger:
            logger.info("✓ Estrategia detectada: ESTÁNDAR")
            logger.debug("No se detectaron keywords especiales - Usando validación estándar")
        return AuditStrategy(base_results, logger)
