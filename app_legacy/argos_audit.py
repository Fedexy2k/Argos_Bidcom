"""
Script de integración: Conecta Módulo 1 (Generador) con Módulo 2 (Auditor).
Parsea el Datasheet y audita el Certificado PDF real.
"""
import json
import sys
import os

# Agregar módulos al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.m1_ingest import DatasheetParser
from modules.m2_audit import CertAuditor
from modules.m2_multiaudit import MultiCertAuditor

# Archivos de prueba (se pueden cambiar por argumentos)
DATASHEET_FILE = "Datasheet caso 2 juguetes.xlsx" 
# Nota: Los certificados se autodetectan si son Juguetes

def print_colored(text, status):
    """Imprime texto con color según el estado (para consola)."""
    colors = {
        "OK": "\033[92m",      # Verde
        "WARNING": "\033[93m", # Amarillo
        "FAIL": "\033[91m",    # Rojo
        "RESET": "\033[0m"
    }
    color = colors.get(status, colors["RESET"])
    print(f"{color}{text}{colors['RESET']}")

def find_certificates_for_toys(directory, specific_id=None):
    """
    Busca certificados de Juguetes y Ftalatos en el directorio.
    Retorna un diccionario con paths.
    """
    certs = {}
    for filename in os.listdir(directory):
        if not filename.endswith(".pdf") and not filename.endswith(".PDF"):
            continue
            
        # Filtro opcional por ID si se provee
        if specific_id and specific_id not in filename:
            continue
            
        lower_name = filename.lower()
        if "juguetes" in lower_name and "ftalatos" not in lower_name:
            certs["SEGURIDAD_JUGUETES"] = os.path.join(directory, filename)
        elif "ftalatos" in lower_name:
            certs["FTALATOS"] = os.path.join(directory, filename)
            
    return certs

def main():
    print("=" * 60)
    print("        ARGOS - Sistema de Auditoria de Certificados")
    print("=" * 60)
    
    # --- PASO 1: Parsear Datasheet ---
    print("\n[1/3] Parseando Datasheet...")
    if not os.path.exists(DATASHEET_FILE):
        print(f"  [ERROR] Archivo no encontrado: {DATASHEET_FILE}")
        return

    try:
        parser = DatasheetParser(DATASHEET_FILE)
        json_data = parser.parse()
        
        print(f"  [OK] SKU: {json_data.get('sku_principal')}")
        print(f"  [OK] Tipo Producto: {json_data.get('tipo_producto')}")
        print(f"  [OK] Certificados Requeridos: {len(json_data.get('certificados_requeridos', []))}")
        
    except Exception as e:
        print(f"  [ERROR] Error parseando Datasheet: {e}")
        return

    # --- PASO 2: Identificar Certificados ---
    print("\n[2/3] Identificando Certificados PDF...")
    pdf_paths = {}
    
    if json_data.get("tipo_producto") == "JUGUETES":
        pdf_paths = find_certificates_for_toys(os.getcwd())
        print(f"  [INFO] Certificado Juguetes: {pdf_paths.get('SEGURIDAD_JUGUETES', 'NO ENCONTRADO')}")
        print(f"  [INFO] Certificado Ftalatos: {pdf_paths.get('FTALATOS', 'NO ENCONTRADO')}")
    else:
        # Lógica para Seguridad Eléctrica (un solo archivo asumido por ahora o hardcoded)
        # Para mantener compatibilidad con el test anterior
        potential_cert = "BIDCOM  (SE)  DJC12795SE - CERTIFICADO 837 - BIDCOM - TCSE-IACSA-0146-382.1.pdf"
        if os.path.exists(potential_cert):
            pdf_paths["SEGURIDAD_ELECTRICA"] = potential_cert
            print(f"  [INFO] Certificado Electrico: {potential_cert}")
    
    # --- PASO 3: Ejecutar Auditoría Múltiple ---
    print("\n[3/3] Ejecutando Auditoria Multiple...")
    auditor = MultiCertAuditor()
    
    # Adaptar para usar audit_multiple con el formato de caminos encontrados
    # El método espera un dict {TIPO: PATH}
    # Pero audit_multiple itera sobre json_data['certificados_requeridos']
    
    # Mapeo rápido para asegurar compatibilidad
    consolidated_report = {
        "status": "OK",
        "details": {}
    }
    
    # Usar lógica custom si es multicertificado, o simple si es uno solo?
    # Mejor usar siempre audit_multiple si implementamos la lógica general
    
    # Construir mapa de caminos basado en lo requerido
    paths_map = {}
    for req in json_data.get("certificados_requeridos", []):
        ctype = req["tipo"]
        if ctype in pdf_paths:
            paths_map[ctype] = pdf_paths[ctype]
            
    final_result = auditor.audit_multiple(json_data, paths_map)

    
    # --- REPORTE CONSOLIDADO ---
    print("\n" + "=" * 60)
    print("                  REPORTE DE AUDITORIA")
    print("=" * 60)
    
    status = final_result.get("status", "UNKNOWN")
    print_colored(f"\n  ESTADO GLOBAL: {status}", status)
    
    original_details = final_result.get("details", {})
    
    for cert_key, cert_res in original_details.items():
        print(f"\n  --- {cert_key} ---")
        c_status = cert_res.get("status", "UNKNOWN")
        print_colored(f"  ESTADO: {c_status}", c_status)
        
        details = cert_res.get("details", {})
        
        if details.get("critical"):
            for msg in details["critical"]:
                print_colored(f"     - {msg}", "FAIL")
        
        if details.get("warnings"):
            for msg in details["warnings"]:
                print_colored(f"     - {msg}", "WARNING")

        if not details.get("critical") and not details.get("warnings"):
             print_colored("     [OK] Sin observaciones.", "OK")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
