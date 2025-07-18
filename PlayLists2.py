import os
import shutil
import requests
from hashlib import md5
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("PlayLists2.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global settings
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}
OUTPUT_DIR = os.path.join(os.getcwd(), "PlayLists2")
TIMEOUT = 30  # Increased timeout
RETRIES = 3
DELAY_BETWEEN_TRIES = 2
MAX_WORKERS = 5

def validate_url(url):
    """Check if URL is accessible"""
    try:
        response = requests.head(url, headers=HEADERS, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {str(e)}")
        return False

def download_file(url, save_path, retries=RETRIES):
    """Download file with robust error handling"""
    if not validate_url(url):
        logger.error(f"Skipping invalid URL: {url}")
        return False

    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{retries}: Downloading {url}")
            
            with requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True) as response:
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                temp_path = save_path + ".tmp"
                with open(temp_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                
                # Verify download completed successfully
                if os.path.getsize(temp_path) > 0:
                    os.replace(temp_path, save_path)
                    file_size = os.path.getsize(save_path)
                    
                    with open(save_path, 'rb') as file:
                        file_hash = md5(file.read()).hexdigest()
                    
                    logger.info(f"Download successful: {save_path} | Size: {file_size} bytes | Hash: {file_hash}")
                    return True
                
                logger.warning(f"Empty file downloaded: {temp_path}")
                os.remove(temp_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(DELAY_BETWEEN_TRIES)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(DELAY_BETWEEN_TRIES)

    logger.error(f"Failed to download after {retries} attempts: {url}")
    return False

def clean_directory(dir_path):
    """Safely clean directory contents"""
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            return True
            
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")
                return False
        return True
    except Exception as e:
        logger.error(f"Directory cleanup failed: {str(e)}")
        return False

def main():
    try:
        logger.info("Starting PlayLists2 download process...")
        
        if not clean_directory(OUTPUT_DIR):
            logger.error("Failed to prepare output directory")
            return False

        # Files to download configuration
        files_config = [
            # M3U Playlists
            ("http://m3u4u.com/m3u/3wk1y24kx7uzdevxygz7", "PlayLists2_1.m3u"),
            ("http://m3u4u.com/m3u/jq2zy9epr3bwxmgwyxr5", "PlayLists2_2.m3u"),
            ("http://m3u4u.com/m3u/782dyqdrqkh1xegen4zp", "PlayLists2_3.m3u"),
            ("https://gitlab.com/josieljefferson12/playlists/-/raw/main/PiauiTV.m3u", "PlayLists2_4.m3u"),
            ("https://gitlab.com/josieljefferson12/playlists/-/raw/main/m3u4u_proton.me.m3u", "PlayLists2_5.m3u"),
            
            # EPG Files
            ("http://m3u4u.com/epg/3wk1y24kx7uzdevxygz7", "PlayLists2_1.xml.gz"),
            ("http://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5", "PlayLists2_2.xml.gz"),
            ("http://m3u4u.com/epg/782dyqdrqkh1xegen4zp", "PlayLists2_3.xml.gz")
        ]

        # Process downloads in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(download_file, url, os.path.join(OUTPUT_DIR, filename)) 
                     for url, filename in files_config]
            
            results = [future.result() for future in as_completed(futures)]
            
            if not all(results):
                failed = results.count(False)
                logger.error(f"Failed to download {failed}/{len(results)} files")
                return False

        logger.info("All downloads completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Main process failed: {str(e)}")
        return False

if __name__ == "__main__":
    exit(0 if main() else 1)
