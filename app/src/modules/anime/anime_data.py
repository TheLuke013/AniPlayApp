import requests
from loguru import logger

def get_anime_by_name(anime_name):
    """
    Busca anime por nome usando a API do AniList
    """
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
        description
        episodes
        status
        averageScore
        genres
        coverImage {
          large
        }
        siteUrl
      }
    }
    '''
    
    variables = {
        'search': anime_name
    }
    
    try:
        response = requests.post('https://graphql.anilist.co', json={
            'query': query,
            'variables': variables
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('Media'):
                logger.info(f"✅ Anime encontrado por nome: {anime_name}")
                return data
            else:
                logger.warning(f"⚠️ Anime não encontrado por nome: {anime_name}")
                return None
        else:
            logger.error(f"❌ Erro na API AniList: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar anime por nome: {e}")
        return None

def get_anime_with_fallback(anime_id, anime_name=None):
    """
    Tenta buscar anime por ID, se falhar busca por nome
    """
    # Primeiro tenta por ID
    anime_data = get_anime_by_id(anime_id)
    
    if (anime_data and 
        anime_data.get('data') and 
        anime_data['data'].get('Media') and 
        anime_data['data']['Media'].get('id') != 0):
        return anime_data
    
    # Se ID falhou ou é 0, tenta por nome
    if anime_name:
        logger.info(f"🔄 ID {anime_id} inválido, tentando buscar por nome: {anime_name}")
        return get_anime_by_name(anime_name)
    
    return None

def get_anime_by_id(anime_id):
    """
    Busca anime por ID específico
    """
    query = '''
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
        description
        episodes
        status
        averageScore
        genres
        coverImage {
          large
        }
        siteUrl
      }
    }
    '''
    
    variables = {
        'id': anime_id
    }
    
    response = requests.post('https://graphql.anilist.co', json={
        'query': query,
        'variables': variables
    })
    
    return response.json()

def get_anime_episodes(anime_id):
    try:
        url = f"http://localhost:4000/api/v2/hianime/anime/{anime_id}/episodes"
        
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

def get_search_anime(search, page=1):
    try:
        url = f"http://localhost:4000/api/v2/hianime/search?q={search}&page={page}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Dados dos animes obtidos com sucesso - Página {page}")
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
        url = f"http://localhost:4000/api/v2/hianime/anime/{anime_id}"
        
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
