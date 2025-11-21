# -*- coding: utf-8 -*-
"""
OAB-BA OnCloud - Login ANTI-DELAY + EXTRAÇÃO AVANÇADA (2025)
Corrigido para demora no clique e redirecionamento JS
"""

import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup, NavigableString, Comment
from playwright.sync_api import sync_playwright

# ================================== CONFIGURAÇÃO ==================================
USERNAME = "cloudn2field"          # ← Seu usuário real
PASSWORD = "cloudn2field"          # ← Sua senha real

LOGIN_URL = "https://oncloud.oab-ba.org.br/index.php/login"
HOME_URL = "https://oncloud.oab-ba.org.br/index.php/site/index"

# ==============================================================================
def wait_for_page_stable(page, timeout=30):
    """Espera a página estabilizar (sem redirecionamentos)"""
    start = time.time()
    last_url = page.url
    stable_time = 0
    while time.time() - start < timeout:
        time.sleep(0.5)
        current_url = page.url
        if current_url == last_url:
            stable_time += 0.5
            if stable_time >= 2:
                return True
        else:
            last_url = current_url
            stable_time = 0
    return False

def extrair_conteudo_avancado(html):
    """Extrai tudo: headers, textos limpos, comentários, links, etc"""
    soup = BeautifulSoup(html, "lxml")

    print("\n" + "="*90)
    print(" EXTRAÇÃO AVANÇADA DO CONTEÚDO (BeautifulSoup + NavigableString + Comment) ".center(90))
    print("="*90)

    # Título
    titulo = soup.title.get_text(strip=True) if soup.title else "Sem título"
    print(f"TÍTULO DA PÁGINA: {titulo}")

    # Saudação / Usuário logado
    saudacao = soup.find(string=re.compile(r"Bem[ -]?vindo|Olá|Advogad[ao]", re.I))
    if saudacao:
        print(f"USUÁRIO LOGADO: {saudacao.strip()}")

    # Todos os headers (h1 a h6)
    print("\nHEADERS ENCONTRADOS:")
    headers = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for h in headers:
        print(f"   {h.name.upper()}: {h.get_text(strip=True)}")

    # Todos os links do menu
    print(f"\nMENU PRINCIPAL ({len(soup.find_all('a', href=True))} links encontrados):")
    for a in soup.find_all("a", href=True):
        texto = a.get_text(strip=True)
        if texto and len(texto) > 3 and texto.lower() not in ["sair", "logout", "fechar"]:
            link = urljoin("https://oncloud.oab-ba.org.br/", a["href"])
            print(f"   • {texto} → {link}")

    # Textos limpos (sem tags, só conteúdo real)
    print(f"\nTEXTOS LIMPOS DA PÁGINA (NavigableString):")
    textos = [t.strip() for t in soup.find_all(string=True)
              if isinstance(t, NavigableString)
              and not isinstance(t, Comment)
              and t.parent.name not in ['script', 'style', 'head', 'title']
              and t.strip()]
    for texto in textos[:30]:  # Mostra só os 30 primeiros
        print(f"   → {texto}")

    # Comentários HTML (útil para debug)
    print(f"\nCOMENTÁRIOS HTML ENCONTRADOS:")
    comentarios = soup.find_all(string=lambda text: isinstance(text, Comment))
    if comentarios:
        for c in comentarios:
            print(f"   <!-- {c.strip()} -->")
    else:
        print("   Nenhum comentário encontrado.")

    print(f"\nEXTRAÇÃO CONCLUÍDA! Total de elementos analisados: {len(soup.find_all())}")
    print("="*90)

# ==============================================================================
def login_oab_oncloud():
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando login no OnCloud OAB-BA...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # ← Mude para True depois que funcionar
            slow_mo=1200,    # ← Aumentado para você ver o clique
            args=["--start-maximized", "--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="pt-BR"
        )

        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")

        page = context.new_page()

        try:
            print(f"[{time.strftime('%H:%M:%S')}] Acessando login...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=90000)

            # Espera Cloudflare
            for i in range(60):
                if any(x in page.content() for x in ["Just a moment", "Checking"]):
                    print(f"   Cloudflare ativo... {i+1}s")
                    time.sleep(1)
                else:
                    print("   Cloudflare passou!")
                    break

            # Espera campo correto (é "user", não "username"!)
            page.wait_for_selector("input[name='user'], input#user", timeout=90000)

            print(f"[{time.strftime('%H:%M:%S')}] Preenchendo credenciais...")
            page.fill("input[name='user']", USERNAME)
            page.fill("input[name='password']", PASSWORD)

            # === NOVA PARTE: ESPERA O BOTÃO FICAR CLICÁVEL ===
            print(f"[{time.strftime('%H:%M:%S')}] Aguardando botão 'Entrar' ficar pronto (até 30s)...")
            page.wait_for_selector("button:has-text('Entrar'), button[type='submit']", state="visible", timeout=30000)

            print(f"[{time.strftime('%H:%M:%S')}] Clicando no botão...")
            page.click("button:has-text('Entrar'), button[type='submit']", timeout=10000)

            # === NOVA PARTE: PROCESSAMENTO PÓS-CLIQUE ===
            print(f"[{time.strftime('%H:%M:%S')}] Processando login (aguardando JS + redirecionamento, até 15s)...")
            time.sleep(15)  # Dá tempo pro JS do ownCloud processar

            # Verifica se login falhou (erro na página)
            content_lower = page.content().lower()
            if "inválido" in content_lower or "erro" in content_lower or "falha" in content_lower:
                print("ERRO: Login falhou! Verifique credenciais ou CAPTCHA.")
                return None

            # Verifica se sucesso (aparece "logout" ou redireciona)
            if "logout" in content_lower or "site/index" in page.url:
                print("LOGIN BEM-SUCEDIDO! (detectado por conteúdo)")
            else:
                print("AVISO: Não redirecionou, mas continuando...")

            # Tenta ir pra home mesmo assim
            print(f"[{time.strftime('%H:%M:%S')}] Indo para home...")
            page.goto(HOME_URL, timeout=60000)
            time.sleep(6)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

            html = page.content()

            # Salva HTML completo
            with open("oab_oncloud_logado.html", "w", encoding="utf-8") as f:
                f.write(html)

            print("HTML da área restrita salvo com sucesso!")

            # === EXTRAÇÃO AVANÇADA ===
            extrair_conteudo_avancado(html)

            return html

        except Exception as e:
            print(f"Erro: {e}")
            page.screenshot(path="erro_final.png")
            print("Screenshot salvo como erro_final.png")
        finally:
            input("\nPressione ENTER para fechar o navegador...")
            browser.close()

# ==============================================================================
if __name__ == "__main__":
    login_oab_oncloud()