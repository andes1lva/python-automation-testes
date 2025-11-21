# -*- coding: utf-8 -*-
"""
OAB-BA OnCloud - VARREDURA TOTAL BONITA E LEGÍVEL (2025)
Saída: terminal colorido + arquivo .txt organizado (sem JSON feio)
"""

import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright
from datetime import datetime

# ================================== CONFIGURAÇÃO ==================================
USERNAME = "cloudn2field"
PASSWORD = "cloudn2field"

LOGIN_URL = "https://oncloud.oab-ba.org.br/index.php/login"
HOME_URL = "https://oncloud.oab-ba.org.br/index.php/site/index"

# ==============================================================================
def salvar_log_texto(conteudo):
    nome_arquivo = f"ONCLOUD_OAB_BA_VARREDURA_COMPLETA_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"\nRELATÓRIO SALVO COMO: {nome_arquivo}\n")

def varredura_bonita(page):
    print("\n" + "═" * 100)
    print(" VARREDURA COMPLETA DO ONCLOUD OAB-BA ".center(100, "█"))
    print("═" * 100 + "\n")

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    log = []
    log.append("═" * 100)
    log.append(" VARREDURA COMPLETA DO ONCLOUD OAB-BA ".center(100))
    log.append(f" Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    log.append(f" URL: {page.url}")
    log.append("═" * 100)
    log.append("")

    # 1. Usuário logado
    usuario = soup.find(string=re.compile(r"Bem[ -]?vindo|Olá|Advogad[ao]", re.I))
    usuario_texto = usuario.strip() if usuario else "Não identificado"
    print(f"USUÁRIO LOGADO: {usuario_texto}")
    log.append(f"USUÁRIO LOGADO: {usuario_texto}")
    log.append("")

    # 2. Pastas
    pastas = []
    for tr in soup.find_all("tr", {"data-type": "dir"}):
        nome = tr.get("data-filename") or "Pasta sem nome"
        link = tr.find("a", href=True)
        link = urljoin(page.url, link["href"]) if link else "Sem link"
        pastas.append({"nome": nome, "link": link})

    print(f"PASTAS ENCONTRADAS: {len(pastas)}")
    log.append(f"PASTAS ENCONTRADAS: {len(pastas)}")
    log.append("-" * 80)
    for p in pastas:
        print(f"   Pasta: {p['nome']}")
        print(f"        Link: {p['link']}\n")
        log.append(f"   Pasta: {p['nome']}")
        log.append(f"        Link: {p['link']}")
        log.append("")

    # 3. Arquivos
    arquivos = []
    for tr in soup.find_all("tr", {"data-type": "file"}):
        nome = tr.get("data-filename", "Arquivo sem nome")
        link_tag = tr.find("a", href=True)
        link = urljoin(page.url, link_tag["href"]) if link_tag else "Sem link"
        tamanho = tr.get("data-size", "Tamanho desconhecido")
        arquivos.append({"nome": nome, "link": link, "tamanho": tamanho})

    print(f"ARQUIVOS ENCONTRADOS: {len(arquivos)}")
    log.append(f"ARQUIVOS ENCONTRADOS: {len(arquivos)}")
    log.append("-" * 80)
    if arquivos:
        for a in arquivos:
            print(f"   Arquivo: {a['nome']} ({a['tamanho']})")
            print(f"         Download: {a['link']}\n")
            log.append(f"   Arquivo: {a['nome']} ({a['tamanho']})")
            log.append(f"         Download: {a['link']}")
            log.append("")
    else:
        print("   Nenhum arquivo encontrado na pasta atual.\n")
        log.append("   Nenhum arquivo encontrado na pasta atual.")
        log.append("")

    # 4. Menu Principal
    print(f"MENU PRINCIPAL:")
    log.append(f"MENU PRINCIPAL:")
    log.append("-" * 80)
    for a in soup.find_all("a", href=True):
        texto = a.get_text(strip=True)
        if texto and len(texto) > 3 and texto.lower() not in ["sair", "logout", "ajuda", "configurações"]:
            link = urljoin("https://oncloud.oab-ba.org.br/", a["href"])
            print(f"   • {texto}")
            print(f"     → {link}\n")
            log.append(f"   • {texto}")
            log.append(f"     → {link}")
            log.append("")

    # 5. Botões e ações
    print(f"BOTÕES E AÇÕES DISPONÍVEIS:")
    log.append(f"BOTÕES E AÇÕES DISPONÍVEIS:")
    log.append("-" * 80)
    botoes = soup.find_all(["button", "input", "a"], {"class": lambda x: x and ("button" in " ".join(x) if x else False)})
    for b in botoes[:20]:
        texto = b.get_text(strip=True) or b.get("value", "Botão sem texto")
        print(f"   Botão: {texto}")
        log.append(f"   Botão: {texto}")

    # Finalização
    log.append("")
    log.append("═" * 100)
    log.append(" VARREDURA CONCLUÍDA COM SUCESSO ".center(100))
    log.append("═" * 100)

    log_texto = "\n".join(log)
    salvar_log_texto(log_texto)

    print("\n" + "█" * 100)
    print(" VARREDURA CONCLUÍDA COM SUCESSO! ".center(100))
    print(" RELATÓRIO GERADO EM TEXTO PURO E BONITO ".center(100))
    print("█" * 100)

# ==============================================================================
def login_e_varrer_bonito():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=800)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        page = context.new_page()

        try:
            page.goto(LOGIN_URL, timeout=90000)
            page.wait_for_selector("input[name='user']", timeout=90000)
            page.fill("input[name='user']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            page.locator("button:has-text('Entrar'), button[type='submit'], button").first.click()

            page.wait_for_function(
                "()=> document.body.innerText.includes('Arquivos') || document.body.innerText.includes('Bem-vindo')",
                timeout=60000
            )

            print("LOGIN BEM-SUCEDIDO! Entrando na área restrita...")
            page.goto(HOME_URL)
            time.sleep(10)

            varredura_bonita(page)

        except Exception as e:
            print(f"Erro: {e}")
            page.screenshot(path="erro_final.png")
        finally:
            input("\nPressione ENTER para fechar o navegador...")
            browser.close()

# ==============================================================================
if __name__ == "__main__":
    login_e_varrer_bonito()