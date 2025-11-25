from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QWidget, QFrame,
                               QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

import json
from loguru import logger

from modules.anime.anime_data import get_anime_info, get_anime_episodes
from modules.anime.animefire_downloader import AnimeFireDownloader

def get_anime_structure(anime):
    anime_info = get_anime_info(anime['id'])
    more_info = anime_info["data"]["anime"]["moreInfo"]
    anime = anime_info["data"]["anime"]["info"]

    return {
        "name": anime.get("name", "Sem título"),
        "status": more_info.get("status", "N/A"),
        "episodes": anime["stats"]["episodes"]["sub"] if "episodes" in anime["stats"] else "?",
        "poster": anime.get("poster", ""),
        "id": anime.get("id", ""),
        "type": anime["stats"].get("type", "N/A"),
        "description": anime.get("description", "Descrição não disponível."),
        "genres": more_info.get("genres", []),
        "studio": more_info.get("studios", "N/A"),
        "duration": more_info.get("duration", "N/A"),
        "year": more_info.get("aired", "N/A")
    }

class EpisodeButton(QPushButton):
    def __init__(self, episode_data, parent=None):
        super().__init__(parent)
        self.episode_data = episode_data
        self.setup_ui()
        
    def setup_ui(self):
        episode_number = self.episode_data.get('number', 0)
        episode_title = self.episode_data.get('title', f'Episódio {episode_number}')
        is_filler = self.episode_data.get('isFiller', False)
        
        # Texto do botão
        filler_text = " (Filler)" if is_filler else ""
        self.setText(f"EP {episode_number}\n{episode_title}{filler_text}")
        
        self.setFixedSize(180, 80)
        self.setStyleSheet("""
            EpisodeButton {
                background: #2a2a2a;
                color: white;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
                text-align: center;
            }
            EpisodeButton:hover {
                background: #333333;
                border: 2px solid #ff7b00;
            }
            EpisodeButton:pressed {
                background: #ff7b00;
            }
        """)
        
        # Tooltip com informações detalhadas
        self.setToolTip(f"Episódio {episode_number}: {episode_title}")

class AnimeDetailsDialog(QDialog):
    def __init__(self, anime, image_loader_callback, parent=None):
        super().__init__(parent)
        self.anime = get_anime_structure(anime)
        self.image_loader_callback = image_loader_callback
        self.episodes_data = None
        self.downloader = AnimeFireDownloader()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setup_ui()
        
        # Carrega os episódios em background
        self.load_episodes()
           
    def setup_ui(self):
        self.setWindowTitle(f"Detalhes - {self.anime.get('name', 'Anime')}")
        self.setFixedSize(900, 700)  # Aumentei o tamanho para caber os episódios
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                border-radius: 15px;
                border: 2px solid #ff7b00;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #ff7b00;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff9500;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Widget de conteúdo que vai dentro da scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # Cabeçalho
        header_widget = self.create_header()
        self.content_layout.addWidget(header_widget)
        
        # Descrição
        description_widget = self.create_description()
        self.content_layout.addWidget(description_widget)
        
        # Informações detalhadas
        details_widget = self.create_details_section()
        self.content_layout.addWidget(details_widget)
        
        # SEÇÃO DE EPISÓDIOS (inicialmente vazia)
        self.episodes_section = self.create_episodes_section()
        self.content_layout.addWidget(self.episodes_section)
        
        # Botões de ação
        buttons_widget = self.create_action_buttons()
        self.content_layout.addWidget(buttons_widget)
        
        self.content_widget.setLayout(self.content_layout)
        scroll_area.setWidget(self.content_widget)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def create_episodes_section(self):
        """Cria a seção de episódios (inicialmente vazia)"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Título da seção
        title_label = QLabel("📺 Episódios")
        title_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }
        """)
        
        # Container para os botões de episódios
        self.episodes_container = QWidget()
        self.episodes_grid = QGridLayout()
        self.episodes_grid.setSpacing(10)
        self.episodes_grid.setContentsMargins(0, 0, 0, 0)
        
        self.episodes_container.setLayout(self.episodes_grid)
        
        # Label de carregamento
        self.episodes_loading_label = QLabel("Carregando episódios...")
        self.episodes_loading_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                text-align: center;
                padding: 20px;
            }
        """)
        self.episodes_loading_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(self.episodes_loading_label)
        layout.addWidget(self.episodes_container)
        
        section.setLayout(layout)
        return section
    
    def load_episodes(self):
        """Carrega os episódios do anime"""
        try:
            anime_episodes = get_anime_episodes(self.anime.get('id'))
            if anime_episodes and "data" in anime_episodes:
                self.episodes_data = anime_episodes["data"]
                logger.info(f"✅ Episódios carregados: {len(self.episodes_data.get('episodes', []))} episódios")
                
                # Atualiza a UI com os episódios
                self.display_episodes()
            else:
                self.show_episodes_error("Não foi possível carregar os episódios.")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar episódios: {e}")
            self.show_episodes_error("Erro ao carregar episódios.")
    
    def display_episodes(self):
        """Exibe os episódios na interface"""
        if not self.episodes_data:
            return
            
        # Remove a mensagem de carregamento
        self.episodes_loading_label.hide()
        
        episodes = self.episodes_data.get('episodes', [])
        total_episodes = self.episodes_data.get('totalEpisodes', 0)
        
        if not episodes:
            self.show_episodes_error("Nenhum episódio disponível.")
            return
        
        # Atualiza o título com a contagem
        episodes_title = f"📺 Episódios ({len(episodes)}/{total_episodes})"
        title_label = self.episodes_section.layout().itemAt(0).widget()
        if isinstance(title_label, QLabel):
            title_label.setText(episodes_title)
        
        # Limpa o grid anterior
        for i in reversed(range(self.episodes_grid.count())): 
            self.episodes_grid.itemAt(i).widget().setParent(None)
        
        # Adiciona os botões de episódios
        row, col = 0, 0
        max_cols = 4  # 4 botões por linha
        
        for episode in episodes:
            episode_btn = EpisodeButton(episode)
            episode_btn.clicked.connect(lambda checked, ep=episode: self.play_episode(ep))
            
            self.episodes_grid.addWidget(episode_btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def show_episodes_error(self, message):
        """Mostra mensagem de erro na seção de episódios"""
        self.episodes_loading_label.setText(message)
        self.episodes_loading_label.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 14px;
                text-align: center;
                padding: 20px;
            }
        """)
    
    def play_episode(self, episode_data):
        """Abre a seleção de servidor para um episódio"""     
        self.open_video_player(episode_data)
    
    def create_header(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # Poster grande
        poster_label = QLabel()
        poster_label.setFixedSize(200, 280)
        poster_label.setStyleSheet("""
            QLabel {
                background: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #444;
            }
        """)
        poster_label.setAlignment(Qt.AlignCenter)
        poster_label.setText("Carregando...")
        
        if self.anime.get('poster'):
            self.image_loader_callback(
                f"{self.anime['id']}_large", 
                self.anime['poster'], 
                poster_label
            )
        
        # Informações principais
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        title_label = QLabel(self.anime.get('name', 'Título não disponível'))
        title_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        title_label.setWordWrap(True)
        
        # Metadados
        metadata_text = f"""
        <p style="color: white; font-size: 14px;">
            <b>Tipo:</b> {self.anime.get('type', 'N/A')}<br>
            <b>Episódios:</b> {self.anime.get('episodes', '?')}<br>
            <b>Status:</b> {self.anime.get('status', 'N/A')}<br>
            <b>Lançamento:</b> {self.anime.get('year', 'N/A')}
        </p>
        """
        metadata_label = QLabel(metadata_text)
        metadata_label.setStyleSheet("background: transparent;")
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(metadata_label)
        info_layout.addStretch()
        info_widget.setLayout(info_layout)
        
        layout.addWidget(poster_label)
        layout.addWidget(info_widget)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_description(self):
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        
        desc_label = QLabel("Descrição")
        desc_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        description_text = self.anime.get('description', 'Descrição não disponível.')
        content_label = QLabel(description_text)
        content_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        
        layout.addWidget(desc_label)
        layout.addWidget(content_label)
        widget.setLayout(layout)
        return widget
    
    def create_details_section(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Gêneros
        if self.anime.get('genres'):
            genres_widget = self.create_info_row("Gêneros", ", ".join(self.anime['genres']))
            layout.addWidget(genres_widget)
        
        # Estúdio
        if self.anime.get('studio'):
            studio_widget = self.create_info_row("Estúdio", self.anime['studio'])
            layout.addWidget(studio_widget)
        
        # Duração
        if self.anime.get('duration'):
            duration_widget = self.create_info_row("Duração", self.anime['duration'])
            layout.addWidget(duration_widget)
        
        widget.setLayout(layout)
        return widget
    
    def create_info_row(self, title, content):
        widget = QWidget()
        layout = QHBoxLayout()
        
        title_label = QLabel(f"{title}:")
        title_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
        """)
        
        content_label = QLabel(content)
        content_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        content_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_action_buttons(self):
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Botão Fechar
        close_btn = QPushButton("✕ Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff7b00;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        layout.addStretch()
        layout.addWidget(close_btn)
        
        widget.setLayout(layout)
        return widget
    
    def open_video_player(self, episode_data):
        """Abre o player de vídeo com streaming"""
        try:
            logger.info("🎬 Iniciando abertura do player de vídeo...")
            
            # Obtém o link do episódio
            episode_link = self.get_anime_episode_link(episode_data, dub=True)
            logger.info(f"🔗 Link do episódio gerado: {episode_link}")
            
            # Obtém links de streaming
            logger.info("🔄 Obtendo links de streaming...")
            streaming_info = self.downloader.obter_links_streaming_episodio(episode_link)
            
            logger.info(f"📋 Resultado da busca por streaming: {streaming_info['success']}")
            
            if streaming_info['success'] and streaming_info['streaming_links']:
                logger.info(f"✅ Links disponíveis: {list(streaming_info['streaming_links'].keys())}")
                
                # Prepara os dados para o player
                video_data = {
                    'streaming_links': streaming_info['streaming_links'],
                    'episode_data': episode_data,
                    'episode_url': episode_link
                }
                
                # Importa e abre o player
                logger.info("🚀 Abrindo player de vídeo...")
                from modules.ui.video_player import VideoPlayerDialog
                player_dialog = VideoPlayerDialog(video_data, self)
                player_dialog.exec()
                
                logger.info("🎉 Player fechado")
                
            else:
                error_msg = streaming_info.get('error', 'Erro desconhecido')
                logger.error(f"❌ Falha ao obter links de streaming: {error_msg}")
                self.show_error_message(
                    "Erro", 
                    f"Não foi possível encontrar links de streaming para este episódio.\n\nErro: {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"💥 Erro inesperado ao abrir player: {e}")
            import traceback
            logger.error(f"📝 Stack trace: {traceback.format_exc()}")
            self.show_error_message("Erro", f"Não foi possível abrir o player: {str(e)}")

    def get_anime_episode_link(self, episode_data, dub=False):
        """Obtém o link do episódio para download"""

        episode_number = episode_data.get('number', 0)
        anime_name = self.anime.get('name', '').lower().replace(' ', '-')
        name = self.downloader.sanitizar_nome_anime(anime_name) 

        if dub:
            return f"https://animefire.plus/animes/{name}-dublado/{episode_number}"
        else:
            return f"https://animefire.plus/animes/{name}/{episode_number}"

    def start_video_playback(self, selection):
        """Inicia a reprodução do vídeo com a seleção do usuário"""
        server = selection['server']
        language = selection['language']
        episode_data = selection['episode_data']
        
        episode_number = episode_data.get('number', 0)
        episode_title = episode_data.get('title', f'Episódio {episode_number}')
        server_name = server.get('serverName', 'Desconhecido')
        server_id = server.get('serverId')
        
        logger.info(f"🎬 Iniciando reprodução:")
        logger.info(f"   Episódio: {episode_number} - {episode_title}")
        logger.info(f"   Idioma: {language}")
        logger.info(f"   Servidor: {server_name} (ID: {server_id})")

    def launch_video_player(self, video_url, episode_data, subtitles, intro, outro, headers, streaming_links=None):
        """Abre o player de vídeo com todos os dados"""
        
        if not video_url:
            self.show_error_message("Erro", "URL do vídeo não disponível.")
            return
        
        # Prepara os dados para o player
        video_data = {
            'video_url': video_url,
            'episode_data': episode_data,
            'subtitles': subtitles,
            'intro': intro,
            'outro': outro,
            'headers': headers,
            'sources': streaming_links["data"].get("sources", []) if streaming_links and "data" in streaming_links else []
        }
        
        try:
            # Importa e cria o player
            from modules.ui.video_player import VideoPlayerDialog
            
            player_dialog = VideoPlayerDialog(video_data, self)
            player_dialog.exec()
            
            logger.info("✅ Player fechado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao abrir player: {e}")
            self.show_error_message("Erro", f"Não foi possível abrir o player: {str(e)}")

    def show_error_message(self, title, message):
        """Mostra uma mensagem de erro"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, title, message)

    def mousePressEvent(self, event):
        """Permite arrastar a janela sem barras de título"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Permite arrastar a janela sem barras de título"""
        if hasattr(self, 'drag_start_position'):
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()