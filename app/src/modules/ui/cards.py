from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                               QHBoxLayout, QPushButton, QDialog, QScrollArea)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Property
from PySide6.QtGui import QMouseEvent, QEnterEvent
from modules.ui.anime_details import AnimeDetailsDialog

class AnimeCard(QFrame):
    def __init__(self, anime, image_loader_callback):
        super().__init__()
        self.anime = anime
        self.image_loader_callback = image_loader_callback
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        self.setFixedSize(200, 300)
        self.setStyleSheet("""
            AnimeCard {
                background: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3a3a3a;
            }
            AnimeCard:hover {
                border: 2px solid #ff7b00;
                background: #333333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Poster do anime
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(180, 220)
        self.poster_label.setStyleSheet("""
            QLabel {
                background: #1a1a1a;
                border-radius: 8px;
                border: 1px solid #444;
            }
        """)
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setText("Carregando...")
        
        # Título do anime
        self.title_label = QLabel(self.anime.get('name', 'Título não disponível'))
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # Informações adicionais
        info_text = f"{self.anime.get('type', 'N/A')} • {self.anime.get('episodes', '?')} episódios"
        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 12px;
                background: transparent;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.poster_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        self.setLayout(layout)
        
        # Carrega a imagem
        if self.anime.get('poster'):
            self.image_loader_callback(
                self.anime['id'], 
                self.anime['poster'], 
                self.poster_label
            )
    
    def setup_animations(self):
        # Animação de escala no hover
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def enterEvent(self, event: QEnterEvent):
        """Quando o mouse entra no card"""
        original_rect = self.geometry()
        scaled_rect = QRect(
            original_rect.x() - 5,
            original_rect.y() - 5,
            original_rect.width() + 10,
            original_rect.height() + 10
        )
        
        self.scale_animation.setStartValue(original_rect)
        self.scale_animation.setEndValue(scaled_rect)
        self.scale_animation.start()
        
        self.setStyleSheet("""
            AnimeCard {
                background: #333333;
                border-radius: 10px;
                border: 2px solid #ff7b00;
            }
        """)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event: QMouseEvent):
        """Quando o mouse sai do card"""
        original_rect = self.geometry()
        normal_rect = QRect(
            original_rect.x() + 5,
            original_rect.y() + 5,
            original_rect.width() - 10,
            original_rect.height() - 10
        )
        
        self.scale_animation.setStartValue(original_rect)
        self.scale_animation.setEndValue(normal_rect)
        self.scale_animation.start()
        
        self.setStyleSheet("""
            AnimeCard {
                background: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3a3a3a;
            }
        """)
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Quando clica no card"""
        if event.button() == Qt.LeftButton:
            self.show_anime_details()
        super().mousePressEvent(event)
    
    def show_anime_details(self):
        """Mostra a janela de detalhes do anime"""
        dialog = AnimeDetailsDialog(self.anime, self.image_loader_callback, self.window())
        dialog.exec()