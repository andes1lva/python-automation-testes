# -*- coding: utf-8 -*-
import time
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime
import csv
import sys

# ===================================================================
# CONFIGURAÇÃO ÚNICA — MUDE APENAS ESSAS 4 LINHAS
# ===================================================================
USERNAME     = "cloudn2field"                          # seu usuário
PASSWORD     = "cloudn2field"                          # sua senha
LOGIN_URL    = "https://oncloud.oab-ba.org.br/index.php/login"   # página de login
START_URL    = "https://oncloud.oab-ba.org.br/index.php/apps/files/"   # URL que abre logo após login (geralmente /apps/files/)
# ===================================================================

# Lista global
todos_arquivos = []
todos_erros    = []

def salvar_relatorio():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    txt_file  = f"VARREDURA_{timestamp}.txt"
    csv_file  = f"ARQUIVOS_{timestamp}.csv"

    # TXT bonito
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("═" * 130 + "\n")
        f.write(" VARREDURA RECURSIVA COMPLETA - ownCloud / Nextcloud ".center(130))
        f.write(f"\n Início: {datetime.now():%d/%m/%Y às %H:%M:%S}\n")
        f.write(f" Total de arquivos encontrados: {len(todos_arquivos)}\n")
        f.write("═" * 130 + "\n\n")

        caminho_atual = ""
        for item in todos_arquivos:
            if item["caminho"] != caminho_atual:
                caminho_atual = item["caminho"]
                f.write(f"\nPasta: {caminho_atual or '/'}\n")
                f.write("─" * 100 + "\n")
            f.write(f"   {item['nome']:60}  |  {item['tamanho']:>12}  |  {item['link']}\n")

        if todos_erros:
            f.write("\n\n" + "!" * 80 + "\n")
            f.write(" PASTAS QUE NÃO FOI POSSÍVEL ENTRAR ".center(80) + "\n")
            f.write("!" * 80 + "\n")
            for e in todos_erros:
                f.write(f"   {e}\n")

    # CSV (Excel)
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Caminho", "Arquivo", "Tamanho", "Link Download", "Data Varredura"])
        for item in todos_arquivos:
            w.writerow([item["caminho"], item["nome"], item["tamanho"], item["link"], datetime.now().strftime("%d/%m/%Y %H:%M")])

    print(f"\nVARREDURA CONCLUÍDA!")
    print(f"   Arquivo TXT → {txt_file}")
    print(f"   Arquivo CSV → {csv_file} (abra no Excel)")
    print(f"   Total de arquivos mapeados: {len(todos_arquivos)}")

def extrair_caminho(url):
    parsed = urlparse(url)
    dir_path = parse_qs(parsed.query).get("dir", [None])[0]
    return dir_path or "/"

def varrer_pasta(page, caminho_atual="/"):
    print(f"   Explorando → {caminho_atual or '/'}")
    time.sleep(1.5)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # === ARQUIVOS ===
    for tr in soup.find_all("tr", {"data-type": "file"}):
        nome = tr.get("data-file") or tr.get("data-filename") or "sem-nome"
        tamanho_raw = tr.get("data-size", "0")
        try:
            tamanho = f"{int(tamanho_raw)/(1024*1024):.2f} MB" if tamanho_raw.isdigit() else tamanho_raw
        except:
            tamanho = "Desconhecido"

        link_tag = tr.find("a", class_="name")
        link = urljoin(page.url, link_tag["href"]) if link_tag else "sem-link"

        todos_arquivos.append({
            "caminho": caminho_atual,
            "nome": nome.strip(),
            "tamanho": tamanho,
            "link": link
        })

    # === PASTAS (recursão) ===
    for tr in soup.find_all("tr", {"data-type": "dir"}):
        nome = tr.get("data-file") or tr.get("data-filename") or "pasta-sem-nome"
        link_tag = tr.find("a", class_="name")
        if not link_tag:
            continue
        link_pasta = urljoin(page.url, link_tag["href"])

        try:
            page.goto(link_pasta, timeout=45000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            novo_caminho = extrair_caminho(page.url)
            varrer_pasta(page, novo_caminho)
        except Exception as e:
            erro = f"{nome} → {str(e)[:120]}"
            todos_erros.append(erro)
            print(f"   Falhou: {nome}")
        finally:
            # Volta para pasta anterior
            try:
                page.go_back()
                page.wait_for_load_state("networkidle")
                time.sleep(1)
            except:
                pass

# ===================================================================
def main():
    with sync_playwright() as p:
        print("Iniciando navegador...")
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        page = context.new_page()

        try:
            # 1. Login
            page.goto(LOGIN_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            page.fill("input[name='user']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            page.keyboard.press("Enter")

            print("Fazendo login...")
            page.wait_for_url("**apps/files**", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(4)

            # 2. Vai para a página inicial de arquivos
            page.goto(START_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            print("Login bem-sucedido! Iniciando varredura recursiva de TODAS as pastas...")
            varrer_pasta(page, "/")

            salvar_relatorio()

        except Exception as e:
            print(f"\nERRO FATAL: {e}")
            page.screenshot(path="ERRO_FATAL.png", full_page=True)
        finally:
            input("\nPressione ENTER para fechar o navegador...")

if __name__ == "__main__":
    main()