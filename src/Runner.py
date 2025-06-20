import asyncio
from playwright.sync_api import sync_playwright
import logging
from pathlib import Path
from datetime import date
import pandas as pd
import os, sys
# Add project root to the system path
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.pardir
    )
)
sys.path.append(PROJECT_ROOT)



from src.service.process_page import run_urls 
from src.service.transaction import get_payloead


today = date.today()
URLS_FILE = f"captured_urls.txt"

def fetch_url():
    """Captura URLs dos lotes e grava em arquivo texto, parando quando encontrar repetições"""
    url_base = "https://www.pestanaleiloes.com.br/procurar-bens?tipoBem=421&localizacao=Tijucas"
    logging.info( f"Capturando URLs da URL base: {url_base}" )
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url_base + "&lotePage=1")
        page.wait_for_selector("#listaLotes", timeout=10000)
        page.wait_for_load_state("networkidle")

        urls = set()
        page_number = 1
        max_pages = 20 
        duplicate_found = False
        
        while page_number <= max_pages and not duplicate_found:
            print(f"Capturando URLs da página {page_number}...")
            current_page_urls = set()


            links = page.locator("#listaLotes a").all()
            for link in links:
                href = link.get_attribute("href")
                if href:
                    full_url = f"https://www.pestanaleiloes.com.br{href}"
                    if full_url in urls:
                        print(f"URL repetida encontrada: {full_url}")
                        duplicate_found = True
                        break
                    current_page_urls.add(full_url)

            if duplicate_found:
                break

            new_urls_count = len(current_page_urls - urls)
            urls.update(current_page_urls)
            print(f"Adicionados {new_urls_count} novos URLs")


            if new_urls_count == 0:
                print("Nenhum novo URL encontrado nesta página. Encerrando captura.")
                break

            page_number += 1
            next_page_url = url_base + f"&lotePage={page_number}"
            

            try:
                page.goto(next_page_url)
                page.wait_for_selector("#listaLotes", timeout=5000)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Erro ao carregar próxima página: {str(e)}")
                break

        browser.close()

        with open(URLS_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(urls))
        
        print(f"Total de URLs capturadas: {len(urls)}")

def read_url_from_file():
    """Lê URLs do arquivo texto"""
    if not Path(URLS_FILE).exists():
        return []
    
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    
    return urls

async def get_full_table():
    """Processa as URLs lidas do arquivo"""
    
    
    urls = read_url_from_file()
    if not urls:
        print("Nenhuma URL encontrada no arquivo. Execute capturar_urls_para_arquivo() primeiro.")
        return
    
    print(f"Processando {len(urls)} URLs...")
    await run_urls(urls)
    


async def get_full_table_fipe(table_path):
    """Processa as URLs lidas do arquivo"""
    logging.info( f"Capturando URLs da URL base: {table_path}")

    df = pd.read_excel(table_path)
    df = df.iloc[1:]


    firts_clum = df.columns[0]

    first_word = (
        df[firts_clum]
        .astype(str)

        .str.lstrip('-')
        .str.upper()
    )

    result = await get_payloead(first_word.tolist())

    return result




def main():
    while True:
        print("\nMenu:")
        print("1. Capturar URLs e gravar em arquivo")
        print("2. Processar URLs do arquivo")
        print("3. Processar dados FIPE")
        print("4. Sair")
        
        choice = input("Escolha uma opção: ")
        
        if choice == "1":
            fetch_url()
        elif choice == "2":

            asyncio.run(get_full_table())
        elif choice == "4":
            break
        elif choice == "3":
            asyncio.run(get_full_table_fipe("dados_capturados.xlsx"))
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()
    
def run():
    try:
        fetch_url()
        asyncio.run(get_full_table())
    except Exception as e:
        print(f"Erro ao executar o script: {str(e)}")