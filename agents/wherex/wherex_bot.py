"""
Automatiza la postulación de oportunidades en el portal Wherex.

Este script inicia sesión en Wherex con las credenciales proporcionadas,
lee un archivo de lista de precios local, busca coincidencias parciales de
productos en las oportunidades de licitación y envía postulaciones de
forma automática. Cada postulación se registra en una hoja de cálculo de
Google Sheets para evitar repeticiones y llevar un historial de acciones.

Requisitos:
 - Python 3.8+.
 - Paquetes: playwright (asyncio), pandas, gspread, oauth2client.
 - Un archivo de credenciales JSON para acceder a Google Sheets.
 - Un archivo CSV con la lista de precios (columnas: Codigo,Descripcion,Precio).
 - Archivos PDF de fichas técnicas de productos en una carpeta `fichas_tecnicas`.

Para ejecutar el script:
1. Instala dependencias: ``pip install playwright pandas gspread oauth2client``
   y ejecuta ``playwright install`` para instalar los navegadores necesarios.
2. Coloca tu ``credentials.json`` de Google API en la misma carpeta.
3. Asegúrate de que el archivo ``lista_precios.csv`` esté presente con el
   formato mencionado.
4. Ejecuta ``python wherex_bot.py``.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.async_api import async_playwright

# ===== CONFIGURACIÓN =====
# Credenciales de Wherex. Las toma de variables de entorno o usa valores por defecto.
WHEREX_USER = os.environ.get("WHEREX_USER", "evaras@firmavb.cl")
WHEREX_PASS = os.environ.get("WHEREX_PASS", "B1h1m4nd2@")

# Ruta al CSV de lista de precios. Debe contener columnas: Codigo, Descripcion, Precio.
LISTA_PRECIOS_PATH = Path(os.environ.get("PRICE_LIST_PATH", "data/lista_precios.csv"))

# ID de la hoja de cálculo de Google Sheets donde se guardará el log de postulaciones.
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1jDDfbLxA4EVv5v_DhtidKg5ZGt35ZvY7uZ1x2fycDM0")

# Nombre del archivo de credenciales de Google para acceder a Sheets.
GOOGLE_CREDENTIALS_FILE = Path(os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json"))


def cargar_lista_precios() -> pd.DataFrame:
    """Carga la lista de precios desde un archivo CSV."""
    if not LISTA_PRECIOS_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de lista de precios: {LISTA_PRECIOS_PATH}")
    return pd.read_csv(LISTA_PRECIOS_PATH)


def conectar_google_sheet():
    """Devuelve una instancia de la hoja de cálculo de Google Sheets para registrar las postulaciones."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(GOOGLE_CREDENTIALS_FILE), scope)
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1


async def login_wherex(page) -> None:
    """Inicia sesión en Wherex con las credenciales definidas."""
    await page.goto("https://login.wherex.com/")
    # Llenar el formulario de inicio de sesión
    await page.fill('input[type="email"]', WHEREX_USER)
    await page.fill('input[type="password"]', WHEREX_PASS)
    await page.click('button[type="submit"]')
    # Esperar a que la navegación y las solicitudes se estabilicen
    await page.wait_for_load_state('networkidle')


async def postular_oportunidad(page, producto: pd.Series) -> None:
    """
    Realiza la postulación en una oportunidad abierta usando los datos del producto.

    Se asume que ya estás en la página de la oportunidad y que solo falta
    completar los campos para adjuntar documentación y enviar la postulación.
    """
    # Haz click en el botón para iniciar la postulación
    await page.click("text=Postular")

    # Adjunta la ficha técnica correspondiente, si existe
    ficha_path = Path("fichas_tecnicas") / f"{producto['Codigo']}.pdf"
    if ficha_path.is_file():
        await page.set_input_files('input[type="file"]', str(ficha_path))
    else:
        print(f"Advertencia: No se encontró ficha técnica para {producto['Codigo']}.")

    # Rellena la descripción
    await page.fill('textarea[name="descripcion"]', str(producto["Descripcion"]))

    # Envía la postulación
    await page.click("text=Enviar")
    # Espera un corto periodo para asegurar que se procese el envío
    await page.wait_for_timeout(2000)


def registrar_postulacion(sheet, producto: pd.Series) -> None:
    """Registra la postulación realizada en Google Sheets."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        fecha,
        producto["Codigo"],
        producto["Descripcion"],
        producto.get("Precio", ""),
        "Postulado en Wherex",
    ])


async def procesar_oportunidades(page, lista_precios: pd.DataFrame, sheet) -> None:
    """
    Recorre todas las oportunidades disponibles en Wherex y postula a aquellas
    que coincidan parcialmente con la lista de precios.
    """
    # Navega a la sección de oportunidades
    await page.goto("https://www.wherex.com/oportunidades")
    await page.wait_for_selector(".oportunidad-item")

    # Obtiene todas las oportunidades en la página
    oportunidades = await page.query_selector_all(".oportunidad-item")
    for oportunidad in oportunidades:
        nombre = await oportunidad.inner_text()
        # Para cada oportunidad, busca un producto cuyo nombre aparezca en la descripción de la oportunidad
        for _, prod in lista_precios.iterrows():
            if prod["Descripcion"].lower() in nombre.lower():
                await oportunidad.click()
                await page.wait_for_load_state('networkidle')
                await postular_oportunidad(page, prod)
                registrar_postulacion(sheet, prod)
                # Vuelve a la lista de oportunidades antes de pasar a la siguiente
                await page.go_back()
                await page.wait_for_load_state('networkidle')
                break  # Evita revisar más productos para la misma oportunidad


async def main() -> None:
    """Función principal que orquesta el proceso completo de postulación."""
    # Carga lista de precios
    lista_precios = cargar_lista_precios()
    # Conecta con Google Sheets
    sheet = conectar_google_sheet()

    # Inicia Playwright y el navegador
    async with async_playwright() as p:
        # Puedes establecer headless=True si no necesitas ver la ejecución
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Inicia sesión en Wherex
        await login_wherex(page)

        # Procesa oportunidades y postula
        await procesar_oportunidades(page, lista_precios, sheet)

        # Cierra el navegador al finalizar
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Proceso interrumpido por el usuario.")
