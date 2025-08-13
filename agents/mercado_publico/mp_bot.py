import os
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

# Load environment variables from .env if present
load_dotenv()

def load_config():
    cfg = {}
    cfg['MP_USER'] = os.getenv('MP_USER')
    cfg['MP_PASS'] = os.getenv('MP_PASS')
    cfg['SHEETS_ID'] = os.getenv('SHEETS_ID')
    cfg['PRICE_LIST_PATH'] = os.getenv('PRICE_LIST_PATH', 'data/lista_precios.csv')
    cfg['TECH_SHEET_DIR'] = os.getenv('TECH_SHEET_DIR', 'fichas_tecnicas')

    config_path = Path(__file__).parent / 'config.toml'
    if config_path.exists() and tomllib:
        with open(config_path, 'rb') as f:
            data = tomllib.load(f)
            if 'mp' in data:
                mp_cfg = data['mp']
                cfg['MP_USER'] = cfg['MP_USER'] or mp_cfg.get('user')
                cfg['MP_PASS'] = cfg['MP_PASS'] or mp_cfg.get('pass')
            if 'sheets' in data:
                sheets_cfg = data['sheets']
                cfg['SHEETS_ID'] = cfg['SHEETS_ID'] or sheets_cfg.get('sheet_id')
            if 'data' in data:
                cfg['PRICE_LIST_PATH'] = data['data'].get('price_list_path', cfg['PRICE_LIST_PATH'])
            if 'files' in data:
                cfg['TECH_SHEET_DIR'] = data['files'].get('tech_sheet_dir', cfg['TECH_SHEET_DIR'])
    return cfg

def load_price_list(path: str):
    return pd.read_csv(path)

def init_sheets(sheet_id: str):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1

def register_postulation(sheet, product):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, product['Codigo'], product['Descripcion'], product['Precio'], 'Postulado en MP'])

async def login_mp(page, user: str, password: str):
    # Navigate to Mercado Publico provider portal login page
    await page.goto('https://proveedores.mercadopublico.cl/')
    await page.fill('input[name="Email"]', user)
    await page.fill('input[name="Password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')

async def postulate(page, product):
    try:
        # Click on the offer button (selector should be updated according to site)
        await page.click("text=Ofertar")
        tech_path = Path(load_config()['TECH_SHEET_DIR']) / f"{product['Codigo']}.pdf"
        if tech_path.exists():
            await page.set_input_files('input[type="file"]', str(tech_path))
        await page.fill('textarea[name="descripcion"]', product['Descripcion'])
        await page.click('text=Enviar')
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error postulating product {product['Codigo']}: {e}")

async def process_opportunities(page, price_list, sheet):
    # Navigate to opportunities list page (update URL as appropriate)
    await page.goto('https://proveedores.mercadopublico.cl/oportunidades')
    await page.wait_for_selector('.opportunity-row')
    opportunities = await page.query_selector_all('.opportunity-row')
    for opp in opportunities:
        name = await opp.inner_text()
        for _, prod in price_list.iterrows():
            if prod['Descripcion'].lower() in name.lower():
                await opp.click()
                await page.wait_for_load_state('networkidle')
                await postulate(page, prod)
                register_postulation(sheet, prod)
                await page.go_back()
                break

async def main():
    cfg = load_config()
    price_list = load_price_list(cfg['PRICE_LIST_PATH'])
    sheet = init_sheets(cfg['SHEETS_ID'])
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await login_mp(page, cfg['MP_USER'], cfg['MP_PASS'])
        await process_opportunities(page, price_list, sheet)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
