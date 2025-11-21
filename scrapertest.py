import requests
import time
from urllib.request import urlopen
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup, NavigableString, Comment
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


url = "https://oncloud.oab-ba.org.br/index.php"#url que irá ser baixada para a coleta de dados
login_url="https://oncloud.oab-ba.org.br" # variável que recebe o login da url
login_data = { #dados  e atributos de acesso à url principal
    "username": "cloudn2field",
    "password": "cloudn2field"
}
html_content = None #vai guardar o HTML final

def wait_for_redirect_stabilize(driver, timeout=15, check_interval=0.5, stable_duration=2):
    start_time = time.time()
    last_url = driver.current_url
    stable_time = 0

    while time.time() - start_time < timeout:
        time.sleep(check_interval)
        current_url = driver.current_url
        if current_url == last_url:
            stable_time += check_interval
            if stable_time >= stable_duration:
                return True
        else:
            last_url = current_url
            stable_time = 0
    raise TimeoutError("Redirecionamento não estabilizou no tempo esperado")



def selenium_login_and_get_html():
    chrome_options = Options()
    #chrome_options.add_argument("--headless") #rodar sem UI

    #Ajustar o caminho do ChromeDriver no ambiente local
    service = Service(executable_path=r"C:\Users\JULIA MONIZ\Documents\python-automation-testes\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(login_url)
        wait_for_redirect_stabilize(driver)
        wait = WebDriverWait(driver, 30)


        user_input = wait.until(EC.presence_of_element_located((By.NAME, "user")))
        user_input.send_keys(login_data["username"])
        
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(login_data["password"])      

        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button[type="submit"]')))
        login_button.click()

        wait_for_redirect_stabilize(driver)
        wait.until(EC.url_contains("index.php"))

        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.container")))

        page_source = driver.page_source
        print("Conteúdo HTML capturado pelo Selenium (primeiros 500 chars):")
        print(page_source[:500])
        with open("pagina_capturada.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        return page_source    
    
    except Exception as e:
        print(f"Erro no Selenium: {e}")
        return None
    
    finally:
        driver.quit()

try:
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'})
        login_response = session.post(login_url, data=login_data)
        login_response.raise_for_status()
        print(login_response.text[:500])

        if login_response.text and "logout" in login_response.text.lower():
            print("Login realizado com sucesso")
            page_response = session.get(url)
            page_response.raise_for_status()
            html_content = page_response.text
            print(html_content[:500])

            needs_login = ('name="user"' in html_content) and ('logout' not in html_content.lower())

            if needs_login:
                print("Site requer login, tentando autenticar...")
                login_response = session.post(login_url, data=login_data)
                login_response.raise_for_status()
                print(login_response.text[:500])

            if login_response.text and "logout" in login_response.text.lower():
                print("Login realizado com sucesso")
                page_response = session.get(url)
                page_response.raise_for_status()
                html_content = page_response.text
                print(html_content[:500])
            else:
                print("Login com request falhou, usando Selenium...")
                html_content = selenium_login_and_get_html()

        if html_content is not None and 'window.location.href' in html_content:
            match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',html_content)

            if match:
                redirect_url = urljoin(url, match.group(1)) 
                print(f"Detectado redirecionamento para {redirect_url}, via requests, usando Selenium...")
                html_content = selenium_login_and_get_html()
                print(html_content[:500])

            else: 
                print("Site não requer login, usando conteúdo obtido direto.")

except requests.exceptions.Timeout:
    print("Timeout ao conectar com o servidor, tentando Selenium...")
    html_content = selenium_login_and_get_html()
except requests.exceptions.ConnectionError:
    print("Erro de conexão, tentando Selenium...")
    html_content = selenium_login_and_get_html()
except requests.exceptions.HTTPError as e:
    print(f"Erro HTTP: {e}, tentando Selenium...")
    html_content = selenium_login_and_get_html()
except requests.exceptions.RequestException as e:
    print(f"Erro de requests: {e}, tentando Selenium...")
    html_content = selenium_login_and_get_html()
except Exception as e:
    print(f"Erro inesperado: {e}, tentando Selenium...")
    html_content = selenium_login_and_get_html()

if not html_content:
    print("Não foi possível obter conteúdo da página após todas as tentativas.")
    exit()

bsObject = BeautifulSoup(html_content, "lxml")

print("Título da página .", bsObject.title.get_text(strip=True) if bsObject.title else "Sem título")

header_tags = ["h1","h2","h3","h4","h5","h6"] #cria um vetor de tags para busca
current_tag = bsObject.find(header_tags) #pega o primeiro título da lista na posição "0" do vetor

while current_tag:
    print(f"{current_tag.name} : {current_tag.get_text(strip=True)}") #exibe nome dos atributos do objeto | strip true elimina os espaços em volta do texto
    next_tag = current_tag.find_next()
    while next_tag and next_tag.name not in header_tags:
        next_tag = next_tag.find_next()
    current_tag = next_tag #atualiza a lista

for header in bsObject.find_all(header_tags):
    print(f"\nHeader: {header.name} -> {header.get_text(strip=True)}")
    for sibling in header.next_siblings:
        if sibling.name:
            print(f"Próximo irmão: {sibling.name}")
            for child in sibling.children:
                if child.name:
                    text = child.get_text(strip=True)
                    print(f"Filho do irmão: {child.name} - text: {text}")

print("\nExtrair textos dos websites(NavigableString)")
for text in bsObject.find_all(string=True): #condicionante para buscar strings no website
    if isinstance(text, NavigableString) and not isinstance(text, Comment): #verifica e valida a existência de texto com navigableString do beautifulsoup
        clean_text = text.strip()
        if clean_text:
            print(clean_text)


print("\nExtrair comentários das tag nos websites(NavigableString)")
for comment in bsObject.find_all(string=lambda text: isinstance(text, Comment)): #condicionante para verificar e trazer os comentários da página
    print(comment)#printa o que encontrou