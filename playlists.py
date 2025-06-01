# Importação de bibliotecas necessárias
import os           # Para operações com arquivos e diretórios
import shutil       # Para operações avançadas com arquivos (não utilizado atualmente)
import requests     # Para fazer requisições HTTP
from hashlib import md5  # Para gerar hash MD5 de verificação
import logging      # Para registro de logs
from concurrent.futures import ThreadPoolExecutor, as_completed  # Para downloads paralelos

# Configuração do sistema de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Cria uma instância do logger

# Constantes de configuração
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Cabeçalho para simular navegador
OUTPUT_DIR = os.getcwd()  # Diretório atual para salvar os arquivos
TIMEOUT = 10  # Tempo limite em segundos para as requisições
RETRIES = 3   # Número de tentativas para cada download
MAX_WORKERS = 5  # Número máximo de downloads paralelos

def validate_url(url):
    """Valida se a URL começa com http:// ou https://"""
    return url.startswith(("http://", "https://"))

def download_file(url, save_path, retries=RETRIES):
    """
    Faz o download de um arquivo com tratamento de erros e tentativas
    Parâmetros:
        url: Endereço do arquivo a ser baixado
        save_path: Caminho local para salvar o arquivo
        retries: Número de tentativas em caso de falha
    Retorna:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    if not validate_url(url):
        logger.error(f"URL inválida: {url}")
        return False

    for attempt in range(retries):
        try:
            logger.info(f"Tentativa {attempt + 1} de {retries}: Baixando de: {url}")
            # Faz a requisição HTTP
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            
            if response.status_code == 200:
                # Salva o conteúdo no arquivo local
                with open(save_path, 'wb') as file:
                    file.write(response.content)

                # Verifica se o arquivo foi salvo corretamente
                if os.path.getsize(save_path) > 0:
                    logger.info(f"Sucesso: {save_path} ({os.path.getsize(save_path)} bytes)")
                    # Calcula hash MD5 para verificação de integridade
                    with open(save_path, 'rb') as file:
                        file_hash = md5(file.read()).hexdigest()
                    logger.info(f"Hash MD5: {file_hash}")
                    return True
                else:
                    logger.error(f"Erro: Arquivo vazio ou corrompido: {save_path}")
            else:
                logger.error(f"Falha ao baixar {url}. Código: {response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao baixar {url}: {e}")
    return False

def main():
    """Função principal que orquestra o processo de download"""
    logger.info("Removendo arquivos antigos...")
    # Remove arquivos antigos antes de baixar os novos
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(('.m3u', '.xml.gz')):  # Somente arquivos de playlist
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
                logger.info(f"Removido: {f}")
            except Exception as e:
                logger.error(f"Erro ao remover {f}: {e}")

    # Dicionário com os arquivos a serem baixados, organizados por tipo
    files_to_download = {
        "m3u": {  # Arquivos de playlist M3U
            "epgbrasil.m3u": "http://m3u4u.com/m3u/3wk1y24kx7uzdevxygz7",
            "epgportugal.m3u": "http://m3u4u.com/m3u/jq2zy9epr3bwxmgwyxr5",
            "epgbrasilportugal.m3u": "http://m3u4u.com/m3u/782dyqdrqkh1xegen4zp",
            "PiauiTV.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/PiauiTV.m3u",
            "m3u@proton.me.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/m3u4u_proton.me.m3u",
            "playlist.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/playlist.m3u",
            "pornstars.m3u": "https://gitlab.com/josieljefferson12/playlists/-/raw/main/pornstars.m3u"
        },
        "xml.gz": {  # Arquivos de guia de programação (EPG)
            "epgbrasil.xml.gz": "http://m3u4u.com/epg/3wk1y24kx7uzdevxygz7",
            "epgportugal.xml.gz": "http://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5",
            "epgbrasilportugal.xml.gz": "http://m3u4u.com/epg/782dyqdrqkh1xegen4zp"
        }
    }

    logger.info("Iniciando downloads...")
    # Usa ThreadPool para downloads paralelos
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        # Envia todas as tarefas de download para execução
        for ext, files in files_to_download.items():
            for filename, url in files.items():
                save_path = os.path.join(OUTPUT_DIR, filename)
                futures.append(executor.submit(download_file, url, save_path))

        # Processa os downloads conforme são completados
        for future in as_completed(futures):
            if not future.result():  # Verifica se algum download falhou
                logger.error("Erro em um dos downloads.")

    logger.info("Downloads concluídos.")

if __name__ == "__main__":
    # Executa a função main quando o script é chamado diretamente
    main()
