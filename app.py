import pdfplumber
import pandas as pd
import re
import os
import streamlit as st
from datetime import datetime # <- Faltaba este import

MESES_MAP = {
    'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12',
    'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04', 'Mayo': '05', 
    'Junio': '06', 'Julio': '07', 'Agosto': '08', 'Septiembre': '09', 
    'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
}

def procesar_resumen(archivo_pdf):
    nombre_archivo = archivo_pdf.name.upper()
    
    # --- DETERMINAR BANCO POR NOMBRE ---
    banco = None
    # <- Faltaba traer los pattern_cuota acá adentro
    if "GALICIA" in nombre_archivo:
        pattern = re.compile(r'^(\d{2}[./]\d{2}[./]\d{2,4})\s+(\d{6}[*K]?)\s+(.*?)\s+([\d\.]+,\d{2})$')
        pattern_cuota = re.compile(r'Cuota\s+(\d+/\d+)', re.IGNORECASE)
        banco = "GALICIA"
    elif "BBVA" in nombre_archivo:
        pattern = re.compile(r'^(\d{2}-[A-Za-z]{3}-\d{2})\s+(.*?)\s+(\d{6})\s+(-?[\d\.]+,\d{2})')
        pattern_cuota = re.compile(r'C\.(\d{2}/\d{2})')
        banco = "BBVA"
    elif "MACRO" in nombre_archivo:
        pattern = re.compile(r'^(\d{2}[.\s][\w\d\s\.]+)\s+(\d{6}[*K]?)\s+(.*?)\s+(-?[\d\.]+,\d{2})$')
        pattern_cuota = re.compile(r'(?:Cuota|C\.)\s*(\d{2}/\d{2})', re.IGNORECASE)
        banco = "MACRO"
    else:
        return False, "Banco no identificado en el nombre del archivo. Recordá que debe decir Galicia, BBVA o Macro."

    rows = [] # <- Faltaba inicializar la lista vacía

    # Abrimos directamente el archivo de Streamlit (archivo_pdf)
    with pdfplumber.open(archivo_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            for line in text.split('\n'):
                line = line.strip()

                if any(x in line for x in ["SU PAGO", "SALDO ANTERIOR", "PAGOS Y AJUSTES", "VTO. ANTERIOR"]): continue
                if "TOTAL CONSUMOS" in line: continue

                match = pattern.match(line)
                if match:
                    fecha_raw, comprobante, detalle, monto_str = match.groups()

                    try:
                        if banco == "MACRO" and "." in fecha_raw: 
                            fecha_f = datetime.strptime(fecha_raw.strip(), '%d.%m.%y').strftime('%d/%m/%Y')
                        elif banco == "MACRO": 
                            partes = fecha_raw.split()
                            mes_num = MESES_MAP.get(partes[1].capitalize()[:3], '01')
                            fecha_f = f"{partes[0]}/{mes_num}/20{partes[2]}"
                        else:
                            fecha_f = fecha_raw 
                    except: fecha_f = fecha_raw

                    match_cuota = pattern_cuota.search(detalle)
                    if match_cuota:
                        cuota_v = match_cuota.group(1)
                        detalle = pattern_cuota.sub('', detalle).strip()
                    else:
                        cuota_v = "-"

                    monto_float = float(monto_str.replace('.', '').replace(',', '.'))
                    
                    if any(x in detalle for x in ["USD", "BRL"]):
                        m_ars, m_usd = None, monto_float
                        detalle = re.sub(r'(USD|BRL)\s+[\d\.,]+', '', detalle).strip()
                    else:
                        m_ars, m_usd = monto_float, None

                    rows.append({
                        "Fecha": fecha_f,
                        "Comprobante": comprobante,
                        "Detalle": detalle.strip(),
                        "Cuota": cuota_v,
                        "Monto": m_ars,
                        "Monto USD": m_usd
                    })

    if rows:
        df = pd.DataFrame(rows)
        # Convertimos el DataFrame directamente a texto CSV en memoria para Streamlit
        csv_generado = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig').encode('utf-8-sig')
        return True, csv_generado
    else:
        return False, "No se encontraron consumos en el PDF que coincidan con el formato."

# ==========================================
# INTERFAZ WEB
# ==========================================

st.set_page_config(page_title="CrediCSV", page_icon="💳")

st.title("💳 CrediCSV: Convertí tu resumen")
st.write("Subí el PDF de tu tarjeta bancaria para transformarlo en un CSV útil para Excel.")

archivo_subido = st.file_uploader("Seleccioná el resumen PDF (Galicia, BBVA o Macro)", type=["pdf"])

if archivo_subido is not None:
    if st.button("Procesar PDF"):
        with st.spinner("Leyendo documento..."):
            exito, resultado = procesar_resumen(archivo_subido)
            
            if exito:
                st.success("¡PDF procesado correctamente!")
                st.download_button(
                    label="⬇️ Descargar archivo CSV",
                    data=resultado,
                    file_name=f"resumen_{archivo_subido.name.split('.')[0]}.csv",
                    mime="text/csv"
                )
            else:
                st.error(resultado)