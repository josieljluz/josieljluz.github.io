import os
import shutil
import requests
from hashlib import md5
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("TiviMate.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações globais
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}
OUTPUT_DIR = os.path.join(os.getcwd(), "TiviMate")
TIMEOUT = 15  # Timeout aumentado para 15 segundos
RETRIES = 3   # Número de tentativas de download
DELAY_BETWEEN_TRIES = 2  # Delay entre tentativas em segundos
MAX_WORKERS = 5  # Número máximo de downloads simultâneos

def validate_url(url):
    """Valida a URL antes de tentar o download."""
    if not url.startswith(("http://", "https://")):
        logger.error(f"URL inválida: {url}")
        return False
    return True

def download_file(url, save_path, retries=RETRIES):
    """Baixa um arquivo com tratamento robusto de erros."""
    if not validate_url(url):
        return False

    for attempt in range(retries):
        try:
            logger.info(f"Tentativa {attempt + 1}/{retries}: Baixando {url}")
            
            with requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True) as response:
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                
                if os.path.getsize(save_path) > 0:
                    with open(save_path, 'rb') as file:
                        file_hash = md5(file.read()).hexdigest()
                    logger.info(f"Sucesso: {save_path} | Tamanho: {os.path.getsize(save_path)} bytes | Hash: {file_hash}")
                    return True
                
                logger.warning(f"Arquivo vazio: {save_path}")
                os.remove(save_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(DELAY_BETWEEN_TRIES)
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            if attempt < retries - 1:
                time.sleep(DELAY_BETWEEN_TRIES)

    logger.error(f"Falha ao baixar após {retries} tentativas: {url}")
    return False

def main():
    try:
        logger.info("Iniciando processo de download para TiviMate...")
        
        # Limpa diretório anterior
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Lista de arquivos para download
        files_config = {
            "m3u": {
                "epgbrasil.m3u": "http://m3u4u.com/m3u/3wk1y24kx7uzdevxygz7",
                "epgportugal.m3u": "http://m3u4u.com/m3u/jq2zy9epr3bwxmgwyxr5",
                "epgbrasilportugal.m3u": "http://m3u4u.com/m3u/782dyqdrqkh1xegen4zp",
                "PiauiTV.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/PiauiTV.m3u",
                "m3u@proton.me.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/m3u4u_proton.me.m3u"
            },
            "xml.gz": {
                "epgbrasil.xml.gz": "http://m3u4u.com/epg/3wk1y24kx7uzdevxygz7",
                "epgportugal.xml.gz": "http://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5",
                "epgbrasilportugal.xml.gz": "http://m3u4u.com/epg/782dyqdrqkh1xegen4zp"
            }
        }

        # Processa downloads em paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for ext, files in files_config.items():
                for filename, url in files.items():
                    save_path = os.path.join(OUTPUT_DIR, filename)
                    futures.append(executor.submit(download_file, url, save_path))
            
            results = [future.result() for future in as_completed(futures)]
            
            if not all(results):
                logger.error("Alguns downloads falharam. Verifique o log.")
                return False

        logger.info("Todos os downloads foram concluídos com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro no processo principal: {str(e)}")
        return False

if __name__ == "__main__":
    exit(0 if main() else 1)
