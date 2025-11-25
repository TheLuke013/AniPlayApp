import os
import requests
from bs4 import BeautifulSoup
import re
import time
import re
import unicodedata
from loguru import logger

class AnimeFireDownloader:
    def __init__(self, qualidade_desejada='F-HD', baixar_todas_qualidades=False, intervalo_entre_downloads=20):
        """
        Inicializa o downloader de animes.
        
        Args:
            qualidade_desejada (str): Qualidade preferida ('SD', 'HD', 'F-HD', 'FullHD')
            baixar_todas_qualidades (bool): Se True, baixa todas as qualidades disponíveis
            intervalo_entre_downloads (int): Intervalo em segundos entre downloads
        """
        self.qualidade_desejada = qualidade_desejada
        self.baixar_todas_qualidades = baixar_todas_qualidades
        self.intervalo_entre_downloads = intervalo_entre_downloads
        self.qualidades_preferidas = ['FullHD', 'F-HD', 'HD', 'SD']
    
    def extrair_links_streaming(self, html):
        """
        Extrai links de streaming direto do HTML da página de download.
        """
        logger.info("🔎 Analisando HTML em busca de links de streaming...")
        
        soup = BeautifulSoup(html, 'html.parser')
        streaming_links = {}
        
        # 1. Procura por tags de vídeo
        video_tags = soup.find_all('video')
        logger.info(f"🎥 Tags <video> encontradas: {len(video_tags)}")
        
        for video in video_tags:
            if video.get('src'):
                streaming_links['direct'] = video['src']
                logger.info(f"📹 Link direto de vídeo encontrado: {video['src'][:100]}...")
        
        # 2. Procura por tags source dentro de video
        source_tags = soup.find_all('source')
        logger.info(f"📼 Tags <source> encontradas: {len(source_tags)}")
        
        for source in source_tags:
            if source.get('src') and source.get('type', '').startswith('video/'):
                qualidade = source.get('title', 'unknown') or source.get('data-quality', 'unknown')
                streaming_links[qualidade] = source['src']
                logger.info(f"🎬 Source encontrado - Qualidade: {qualidade}, URL: {source['src'][:100]}...")
        
        # 3. Procura por iframes (players externos)
        iframe_tags = soup.find_all('iframe')
        logger.info(f"🖼️ Tags <iframe> encontradas: {len(iframe_tags)}")
        
        for iframe in iframe_tags:
            if iframe.get('src'):
                streaming_links['iframe'] = iframe['src']
                logger.info(f"📺 Iframe encontrado: {iframe['src'][:100]}...")
        
        # 4. Procura por links de download direto (fallback)
        download_links = soup.find_all('a', href=True)
        video_download_links = []
        
        for link in download_links:
            href = link['href']
            if any(ext in href.lower() for ext in ['.mp4', '.m3u8', '.mkv', '.avi', '.webm']):
                qualidade = link.text.strip() or 'download'
                streaming_links[qualidade] = href
                video_download_links.append(qualidade)
        
        if video_download_links:
            logger.info(f"📥 Links de download de vídeo encontrados: {video_download_links}")
        
        logger.info(f"📊 Total de links de streaming encontrados: {len(streaming_links)}")
        return streaming_links

    def obter_links_streaming_episodio(self, link_episodio):
        """
        Obtém links de streaming para um episódio.
        
        Args:
            link_episodio (str): Link do episódio no AnimeFire
            
        Returns:
            dict: Informações de streaming
        """
        logger.info(f"🔍 Buscando links de streaming para: {link_episodio}")
        
        try:
            # Primeiro: tenta acessar a página do episódio diretamente
            logger.info(f"📡 Acessando página do episódio...")
            response = requests.get(link_episodio, timeout=10)
            logger.info(f"📄 Status da página do episódio: {response.status_code}")
            
            if response.status_code == 200:
                streaming_links = self.extrair_links_streaming(response.text)
                logger.info(f"🔗 Links encontrados na página do episódio: {list(streaming_links.keys())}")
                
                # Se não encontrou links diretos, tenta extrair da página de download
                if not streaming_links:
                    logger.info("🔄 Nenhum link direto encontrado, tentando página de download...")
                    nome_obra, numero_episodio = self.extrair_info_do_link(link_episodio)
                    logger.info(f"📝 Info extraída - Nome: {nome_obra}, Episódio: {numero_episodio}")
                    
                    if nome_obra and numero_episodio:
                        link_download = self.modificar_link_para_download(nome_obra, numero_episodio)
                        logger.info(f"📥 Link de download: {link_download}")
                        
                        download_response = requests.get(link_download, timeout=10)
                        logger.info(f"📄 Status da página de download: {download_response.status_code}")
                        
                        if download_response.status_code == 200:
                            streaming_links = self.extrair_links_streaming(download_response.text)
                            logger.info(f"🔗 Links encontrados na página de download: {list(streaming_links.keys())}")
                        else:
                            logger.warning(f"⚠️ Erro ao acessar página de download: {download_response.status_code}")
                    else:
                        logger.warning("⚠️ Não foi possível extrair informações do link")
                
                if streaming_links:
                    logger.info(f"✅ Links de streaming obtidos com sucesso: {len(streaming_links)} qualidades")
                    return {
                        'success': True,
                        'streaming_links': streaming_links,
                        'episode_url': link_episodio
                    }
                else:
                    logger.warning("❌ Nenhum link de streaming encontrado")
                    return {
                        'success': False,
                        'error': 'Nenhum link de streaming encontrado'
                    }
            else:
                logger.error(f"❌ Erro ao acessar página do episódio: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Erro ao acessar página: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Timeout ao acessar a página")
            return {
                'success': False,
                'error': 'Timeout ao acessar a página'
            }
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sanitizar_nome_anime(self, nome_anime):
        """
        Remove caracteres especiais e sanitiza o nome do anime para URLs.
        
        Args:
            nome_anime (str): Nome original do anime
            
        Returns:
            str: Nome sanitizado para uso em URLs
        """
        # Remover acentos e caracteres especiais
        nome_normalizado = unicodedata.normalize('NFKD', nome_anime)
        nome_sem_acentos = ''.join([c for c in nome_normalizado if not unicodedata.combining(c)])
        
        # Remover parênteses e seu conteúdo
        nome_sem_parenteses = re.sub(r'\([^)]*\)', '', nome_sem_acentos)
        
        # Remover colchetes e seu conteúdo
        nome_sem_colchetes = re.sub(r'\[[^\]]*\]', '', nome_sem_parenteses)
        
        # Remover chaves e seu conteúdo
        nome_sem_chaves = re.sub(r'\{[^}]*\}', '', nome_sem_colchetes)
        
        # Substituir caracteres especiais por hífen
        nome_limpo = re.sub(r'[^\w\s-]', '', nome_sem_chaves)
        
        # Substituir múltiplos espaços por um único hífen
        nome_limpo = re.sub(r'[-\s]+', '-', nome_limpo)
        
        # Remover hífens no início e fim
        nome_limpo = nome_limpo.strip('-')
        
        # Converter para minúsculas
        nome_limpo = nome_limpo.lower()
        
        # Remover "dublado" duplicado se existir
        nome_limpo = re.sub(r'-dublado-dublado$', '-dublado', nome_limpo)
        
        return nome_limpo

    def extrair_info_do_link(self, link):
        """
        Extrai nome da obra e número do episódio a partir do link.
        
        Args:
            link (str): URL do episódio no AnimeFire
            
        Returns:
            tuple: (nome_obra, numero_episodio) ou (None, None) se não encontrar
        """
        match = re.search(r'animes/([^/]+)/(\d+)', link)
        if match:
            nome_obra = match.group(1)
            numero_episodio = match.group(2)
            return nome_obra, numero_episodio
        return None, None
    
    def modificar_link_para_download(self, nome_obra, numero_episodio):
        """
        Modifica o link para o link de download.
        
        Args:
            nome_obra (str): Nome da obra
            numero_episodio (str): Número do episódio
            
        Returns:
            str: Link para a página de download
        """
        return f'https://animefire.plus/download/{nome_obra}/{numero_episodio}'
    
    def extrair_links_de_qualidade(self, html):
        """
        Extrai links das qualidades disponíveis do HTML.
        
        Args:
            html (str): Conteúdo HTML da página de download
            
        Returns:
            dict: Dicionário com as qualidades como chaves e links como valores
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = {}
        qualidade_tags = soup.find_all('a', href=True)
        
        for tag in qualidade_tags:
            qualidade_texto = tag.text.strip()
            if qualidade_texto in ['SD', 'HD', 'F-HD', 'FullHD']:
                links[qualidade_texto] = tag['href']
                
        return links
    
    def baixar_video(self, url, caminho_do_arquivo):
        """
        Baixa e salva o vídeo no caminho especificado.
        
        Args:
            url (str): URL do vídeo para download
            caminho_do_arquivo (str): Caminho onde o arquivo será salvo
            
        Returns:
            bool: True se o download foi bem-sucedido, False caso contrário
        """
        try:
            resposta = requests.get(url, stream=True)
            if resposta.status_code == 200:
                os.makedirs(os.path.dirname(caminho_do_arquivo), exist_ok=True)
                
                with open(caminho_do_arquivo, 'wb') as f:
                    for chunk in resposta.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f'✅ Vídeo salvo em: {caminho_do_arquivo}')
                return True
            else:
                print(f'❌ Falha ao baixar o vídeo de {url} - Status: {resposta.status_code}')
                return False
                
        except Exception as e:
            print(f'❌ Erro ao baixar o vídeo: {e}')
            return False
    
    def processar_qualidades(self, links_de_qualidade, nome_obra, numero_episodio):
        """
        Processa e baixa as qualidades disponíveis.
        
        Args:
            links_de_qualidade (dict): Links das qualidades disponíveis
            nome_obra (str): Nome da obra
            numero_episodio (str): Número do episódio
        """
        if self.baixar_todas_qualidades:
            # Baixa todas as qualidades disponíveis
            for qualidade, link in links_de_qualidade.items():
                caminho_do_arquivo = f'anime_fire/{nome_obra}/{numero_episodio}_{qualidade.lower()}.mp4'
                print(f'📥 Baixando qualidade {qualidade}...')
                self.baixar_video(link, caminho_do_arquivo)
        else:
            # Tenta baixar a qualidade desejada
            if self.qualidade_desejada in links_de_qualidade:
                caminho_do_arquivo = f'anime_fire/{nome_obra}/{numero_episodio}_{self.qualidade_desejada.lower()}.mp4'
                print(f'📥 Baixando qualidade {self.qualidade_desejada}...')
                self.baixar_video(links_de_qualidade[self.qualidade_desejada], caminho_do_arquivo)
            else:
                # Se a qualidade desejada não estiver disponível, baixa a melhor disponível
                for qualidade in self.qualidades_preferidas:
                    if qualidade in links_de_qualidade:
                        caminho_do_arquivo = f'anime_fire/{nome_obra}/{numero_episodio}_{qualidade.lower()}.mp4'
                        print(f'📥 Qualidade {self.qualidade_desejada} não disponível. Baixando {qualidade}...')
                        self.baixar_video(links_de_qualidade[qualidade], caminho_do_arquivo)
                        break
    
    def baixar_episodio(self, link_original):
        """
        Baixa um episódio específico.
        
        Args:
            link_original (str): Link original do episódio
            
        Returns:
            bool: True se o download foi bem-sucedido, False caso contrário
        """
        print(f'\n🎌 Processando episódio: {link_original}')
        
        # Extraindo nome da obra e número do episódio
        nome_obra, numero_episodio = self.extrair_info_do_link(link_original)
        
        if not nome_obra or not numero_episodio:
            print('❌ Não foi possível extrair as informações do link original.')
            return False
        
        # Modificando o link para o link de download
        link_download = self.modificar_link_para_download(nome_obra, numero_episodio)
        print(f'🔗 Link de download: {link_download}')
        
        # Fazendo a requisição à página de download
        try:
            response = requests.get(link_download)
            if response.status_code == 200:
                # Extraindo links das qualidades disponíveis
                links_de_qualidade = self.extrair_links_de_qualidade(response.text)
                
                if not links_de_qualidade:
                    print('❌ Nenhum link de download encontrado.')
                    return False
                
                print(f'📊 Qualidades disponíveis: {list(links_de_qualidade.keys())}')
                
                # Processando e baixando as qualidades
                self.processar_qualidades(links_de_qualidade, nome_obra, numero_episodio)
                return True
            else:
                print(f'❌ Não foi possível acessar a página de download. Status: {response.status_code}')
                return False
                
        except Exception as e:
            print(f'❌ Erro ao acessar a página de download: {e}')
            return False
    
    def baixar_lista_episodios(self, links_episodios):
        """
        Baixa uma lista de episódios.
        
        Args:
            links_episodios (list): Lista de links dos episódios
        """
        print(f'🎯 Iniciando download de {len(links_episodios)} episódio(s)')
        print(f'⚙️  Configurações: Qualidade={self.qualidade_desejada}, Todas as qualidades={self.baixar_todas_qualidades}')
        
        for i, link_original in enumerate(links_episodios, 1):
            link_original = link_original.strip()
            if not link_original:
                continue
                
            print(f'\n📋 Episódio {i} de {len(links_episodios)}')
            
            # Baixar o episódio
            self.baixar_episodio(link_original)
            
            # Aguardar intervalo entre downloads (exceto para o último episódio)
            if i < len(links_episodios):
                print(f'⏳ Aguardando {self.intervalo_entre_downloads} segundos antes do próximo download...')
                time.sleep(self.intervalo_entre_downloads)
        
        print('\n🎉 Todos os downloads foram concluídos!')