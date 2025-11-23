import requests
from loguru import logger

def get_search_anime(search, page=1):
    try:
        url = f"http://localhost:4000/api/v2/hianime/search?q={search}&page={page}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Dados dos animes obtidos com sucesso")
            return data
        else:
            logger.error(f"❌ Erro na API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão: {e}")
        return None

def get_animes_home_page():
    try:
        url = f"http://localhost:4000/api/v2/hianime/home"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Dados dos animes obtidos com sucesso")
            return data
        else:
            logger.error(f"❌ Erro na API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão: {e}")
        return None

def get_anime_info(anime_id):
    try:
        url = f"http://localhost:4000/api/anime/{anime_id}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Dados do anime {anime_id} obtidos com sucesso")
            return data
        else:
            logger.error(f"❌ Erro na API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão: {e}")
        return None
