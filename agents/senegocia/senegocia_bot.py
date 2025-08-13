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
    # environment variables
    cfg['SENEGOCIA_USER'] = os.getenv('SENEGOCIA_USER')
    cfg['SENEGOCIA_PASS'] = os.getenv('SENEGOCIA_PASS')
    cfg['SHEETS_ID'] = os.getenv('SHEETS_ID')
    cfg['PRICE_LIST_PATH'] = os.getenv('PRICE_LIST_PATH', 'data/lista_precios.csv')
    cfg['TECH_SHEET_DIR'] = os.getenv('TECH_SHEET_DIR', 'fichas_tecnicas')

    # attempt to read config.toml if environment variables are missing
    config_path = Path(__file__).parent / 'config.toml'
    if config_path.exists() and tomllib:
        with open(config_path, 'rb') as f:
            data = tomllib.load(f)
            if 'senegocia' in data:
                sen_cfg = data['senegocia']
                cfg['SENEGOCIA_USER'] = cfg['SENEGOCIA_USER'] or sen_cfg.get('user')
                cfg['SENEGOCIA_PASS'] = cfg['SENEGOCIA_PASS'] or sen_cfg.get('pass')
            if 'sheets' in data:
                sheets_cfg = data['sheets']
                cfg['SHEETS_ID'] = cfg['SHEETS_ID'] or sheets_cfg.get('sheet_id')
            if 'data' in data:
                data_cfg = data['data']
                cfg['PRICE_LIST_PATH'] = data_cfg.get('price_list_path', cfg['PRICE_LIST_PATH'])
            if 'files' in data:
                files_cfg = data['files']
                cfg['TECH_SHEET_DIR'] = files_cfg.get('tech_sheet_dir', cfg['TECH_SHEET_DIR'])
    return cfg

def load_price_list(path: str):
    return pd.read_csv(path)

def init_sheets(sheet_id):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1

def register_postulation(sheet, product_code, description, price):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, product_code, description, price, 'Postulado en Senegocia'])

async def login_senegocia(page, user, password):
    # Navigate to login page
    await page.goto("https://portal.senegocia.com/")
    await page.fill('input[name="email"]', user)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')

async def postulate_opportunity(page, product):
    # Example placeholder: user must fill actual selectors; this is a template
    try:
        await page.click("text=Postular")  # open postulate modal
        # Upload technical sheet if exists
        tech_file = f"{product['Codigo']}.pdf"
        tech_path = Path(load_config()['TECH_SHEET_DIR']) / tech_file
        if tech_path.exists():
            await page.set_input_files('input[type="file"]', str(tech_path))
        await page.fill('textarea[name="descripcion"]', product['Descripcion'])
        await page.click("text=Enviar")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error postulating product {product['Codigo']}: {e}")

async def process_opportunities(page, price_list, sheet):
    # Navigate to opportunities page; adjust the URL accordingly
    await page.goto("https://portal.senegocia.com/oportunidades")
    await page.wait_for_selector(".oportunidad-item")
    opportunities = await page.query_selector_all(".oportunidad-item")
    for opp in opportunities:
        name = await opp.inner_text()
        for _, prod in price_list.iterrows():
            if prod['Descripcion'].lower() in name.lower():
                await opp.click()
                await page.wait_for_load_state('networkidle')
                await postulate_opportunity(page, prod)
                register_postulation(sheet, prod['Codigo'], prod['Descripcion'], prod['Precio'])
                # go back to list after postulating
                await page.go_back()
                break

async def main():
    cfg = load_config()
    price_list = load_price_list(cfg['PRICE_LIST_PATH'])
    sheet = init_sheets(cfg['SHEETS_ID'])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await login_senegocia(page, cfg['SENEGOCIA_USER'], cfg['SENEGOCIA_PASS'])
        await process_opportunities(page, price_list, sheet)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
