import os
import shutil
import requests
from hashlib import md5
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import time

# Configurações globais
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "*/*",
    "Connection": "keep-alive"
}
OUTPUT_DIR = os.path.join(os.getcwd(), "iMPlayer")
TIMEOUT = 30  # Timeout aumentado para 30 segundos
RETRIES = 3  # Número de tentativas de download
MAX_WORKERS = 5  # Número máximo de threads para downloads paralelos

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.getcwd(), "iMPlayer_download.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_file(url, save_path, retries=RETRIES):
    """
    Baixa um arquivo da URL fornecida e sobrescreve se já existir.
    """
    for attempt in range(retries):
        try:
            logger.info(f"Tentativa {attempt + 1} de {retries}: Baixando {url}")
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
            response.raise_for_status()

            # Garante que o diretório de destino exista
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Salva o conteúdo do arquivo
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            # Verifica se o arquivo foi salvo corretamente
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                logger.info(f"Arquivo salvo com sucesso: {save_path} ({os.path.getsize(save_path)} bytes)")
                
                # Calcula o hash MD5 do arquivo
                with open(save_path, 'rb') as file:
                    file_hash = md5(file.read()).hexdigest()
                logger.info(f"Hash MD5 do arquivo: {file_hash}")
                return True
            else:
                logger.error(f"Erro: Arquivo vazio ou corrompido: {save_path}")
                os.remove(save_path)  # Remove arquivo inválido
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar {url}: {str(e)}")
            time.sleep(2)  # Espera antes de tentar novamente
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar {url}: {str(e)}")
            time.sleep(2)

    logger.error(f"Falha ao baixar {url} após {retries} tentativas.")
    return False

def main():
    try:
        # Remove a pasta iMPlayer antes de baixar os arquivos
        logger.info("Limpando diretório anterior...")
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Lista de arquivos para download
        files_to_download = {
            "m3u": [
                ("http://m3u4u.com/m3u/3wk1y24kx7uzdevxygz7", "iMPlayer_1.m3u"),
                ("http://m3u4u.com/m3u/jq2zy9epr3bwxmgwyxr5", "iMPlayer_2.m3u"),
                ("http://m3u4u.com/m3u/782dyqdrqkh1xegen4zp", "iMPlayer_3.m3u"),
                ("https://gitlab.com/josieljefferson12/playlists/-/raw/main/PiauiTV.m3u", "iMPlayer_4.m3u"),
                ("https://gitlab.com/josieljefferson12/playlists/-/raw/main/m3u4u_proton.me.m3u", "iMPlayer_5.m3u")
            ],
            "xml.gz": [
                ("http://m3u4u.com/epg/3wk1y24kx7uzdevxygz7", "iMPlayer_1.xml.gz"),
                ("http://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5", "iMPlayer_2.xml.gz"),
                ("http://m3u4u.com/epg/782dyqdrqkh1xegen4zp", "iMPlayer_3.xml.gz")
            ]
        }

        # Processa o download dos arquivos
        logger.info("Iniciando download dos arquivos...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for ext, urls in files_to_download.items():
                for url, filename in urls:
                    save_path = os.path.join(OUTPUT_DIR, filename)
                    futures.append(executor.submit(download_file, url, save_path))

            # Verifica os resultados
            success = all(future.result() for future in as_completed(futures))
            
            if not success:
                logger.error("Alguns downloads falharam. Verifique os logs para mais detalhes.")
                return False

        logger.info("Todos os downloads foram concluídos com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro inesperado no processo principal: {str(e)}")
        return False

if __name__ == "__main__":
    if not main():
        exit(1)