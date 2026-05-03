import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Creo un diccionario de meses para los bancos que no me trae el mes numerico.
MESES_MAP = {
    'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12',
    'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04', 'Mayo': '05', 
    'Junio': '06', 'Julio': '07', 'Agosto': '08', 'Septiembre': '09', 
    'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
}

def procesar_resumen(ruta_pdf):
    if not ruta_pdf:
        return
        
    nombre_archivo = os.path.basename(ruta_pdf).upper()
    rows = []
    
    # --- DETERMINAR BANCO POR NOMBRE ---
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
        print("Banco no identificado en el nombre del archivo.")
        return

def seleccionar_y_correr():
    root = tk.Tk()                      # Configuramos la ventanita oculta de Tkinter
    root.withdraw()                     # Oculta la ventana principal pequeña
    root.attributes("-topmost", True)   # La pone al frente de todo

    print("Esperando selección de archivo...")
    
    # Abrimos el selector de archivos
    file_path = filedialog.askopenfilename(
        title="Seleccioná el resumen PDF (Galicia, BBVA o Macro)",
        filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
    )

    if file_path:
        print(f"Procesando: {file_path}")
        procesar_resumen(file_path)
    else:
        print("No seleccionaste ningún archivo.")

if __name__ == "__main__":
    seleccionar_y_correr()
