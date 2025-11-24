from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QWidget, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

import json
from loguru import logger

from modules.anime.anime_data import get_anime_info, get_anime_episodes

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

class AnimeDetailsDialog(QDialog):
    def __init__(self, anime, image_loader_callback, parent=None):
        super().__init__(parent)
        self.anime = get_anime_structure(anime)
        self.image_loader_callback = image_loader_callback
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        self.setup_ui()
           
    def setup_ui(self):
        self.setWindowTitle(f"Detalhes - {self.anime.get('name', 'Anime')}")
        self.setFixedSize(800, 600)
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
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Cabeçalho
        header_widget = self.create_header()
        content_layout.addWidget(header_widget)
        
        # Descrição
        description_widget = self.create_description()
        content_layout.addWidget(description_widget)
        
        # Informações detalhadas
        details_widget = self.create_details_section()
        content_layout.addWidget(details_widget)
        
        # Botões de ação
        buttons_widget = self.create_action_buttons()
        content_layout.addWidget(buttons_widget)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
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
        
        # Classificação (se disponível)
        if self.anime.get('rating'):
            rating_widget = self.create_info_row("Classificação", self.anime['rating'])
            layout.addWidget(rating_widget)
        
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
        
        # Botão Fechar (agora é o principal)
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
        
        # Botão Assistir
        watch_btn = QPushButton("🎬 Assistir Anime")
        watch_btn.setStyleSheet("""
            QPushButton {
                background: #ff7b00;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff9500;
            }
        """)
        watch_btn.clicked.connect(self.watch_anime)
        
        layout.addStretch()
        layout.addWidget(close_btn)
        layout.addWidget(watch_btn)
        
        widget.setLayout(layout)
        return widget
    
    def watch_anime(self):
        """Abre o player do anime"""
        print(f"Iniciando anime: {self.anime.get('name')}")
        
        anime_episodes = get_anime_episodes(self.anime.get('id'))
        if anime_episodes and "data" in anime_episodes:
            logger.info(json.dumps(anime_episodes["data"], indent=4, ensure_ascii=False))

        self.accept()
    
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