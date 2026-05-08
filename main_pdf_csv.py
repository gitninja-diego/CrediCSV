import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime

MESES_BBVA = {
    'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
}

def procesar_resumen(ruta_pdf):
    nombre_archivo = os.path.basename(ruta_pdf).upper()
    rows = []
    
    if "GALICIA" in nombre_archivo:
        pattern = re.compile(r'^(\d{2}[./]\d{2}[./]\d{2,4})\s+(\d{6}[*K]?)\s+(.*?)\s+([\d\.]+,\d{2})$')
        pattern_cuota = re.compile(r'Cuota\s+(\d+/\d+)', re.IGNORECASE)
        banco = "GALICIA"
    elif "BBVA" in nombre_archivo:
        # REGEX CORREGIDA PARA BBVA:
        # Soporta montos negativos (-), montos USD y espacios variables
        # Estructura: Fecha | Detalle... | Cupón (6 dig) | Monto (puede tener - delante)
        pattern = re.compile(r'^(\d{2}-[A-Za-z]{3}-\d{2})\s+(.*?)\s+(\d{6})\s+(-?[\d\.]+,\d{2})')
        pattern_cuota = re.compile(r'C\.(\d{2}/\d{2})')
        banco = "BBVA"
    else: return

    leer_activado = False 

    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            for line in text.split('\n'):
                line = line.strip()

                if banco == "BBVA":
                    if "Sus pagos y ajustes realizados" in line:
                        leer_activado = True
                    # Detenemos la lectura si llegamos a los totales para no duplicar
                    if "TOTAL CONSUMOS" in line:
                        leer_activado = False
                    if not leer_activado: continue

                match = pattern.match(line)
                if match:
                    if banco == "GALICIA":
                        fecha_raw, comprobante, detalle, monto_str = match.groups()
                    else: # BBVA
                        fecha_raw, detalle, comprobante, monto_str = match.groups()

                    # --- FORMATEAR FECHA ---
                    try:
                        if banco == "GALICIA":
                            sep = '.' if '.' in fecha_raw else '/'
                            fmt = f'%d{sep}%m{sep}%y' if len(fecha_raw) <= 8 else f'%d{sep}%m{sep}%Y'
                            fecha_f = datetime.strptime(fecha_raw, fmt).strftime('%d/%m/%Y')
                        else: # BBVA
                            dia, mes_abr, anio = fecha_raw.split('-')
                            mes_num = MESES_BBVA.get(mes_abr.capitalize(), '01')
                            fecha_f = f"{dia}/{mes_num}/20{anio}"
                    except: fecha_f = fecha_raw

                    # --- PROCESAR CUOTAS ---
                    match_cuota = pattern_cuota.search(detalle)
                    if match_cuota:
                        cuota_v = match_cuota.group(1)
                        detalle = pattern_cuota.sub('', detalle).strip()
                    else:
                        cuota_v = "-"

                    # --- MONEDA Y MONTO (Soporta Negativos) ---
                    # Reemplazamos puntos de miles y cambiamos coma por punto
                    monto_limpio = monto_str.replace('.', '').replace(',', '.')
                    monto_float = float(monto_limpio)
                    
                    m_ars, m_usd = (None, monto_float) if "USD" in detalle else (monto_float, None)
                    
                    # Limpiar el detalle de rastros de USD o cuotas
                    detalle_clean = re.sub(r'USD\s+[\d\.,]+', '', detalle).strip()

                    rows.append({
                        "Fecha": fecha_f,
                        "Comprobante": comprobante,
                        "Detalle": detalle_clean,
                        "Cuota": cuota_v,
                        "Monto": m_ars,
                        "Monto USD": m_usd
                    })

    if rows:
        df = pd.DataFrame(rows)
        # Exportar
        df.to_csv(f"resumen_{banco.lower()}.csv", index=False, sep=';', decimal=',', encoding='utf-8-sig')
        print(f"\n--- PROCESADO {banco} OK ---")
        print(df.to_string(index=False, na_rep=''))
    else:
        print("No se detectaron filas. Revisar logs.")

# Ejecutar
procesar_resumen('PDF/BBVA_VISA_RESUMEN_MAY26.pdf')
