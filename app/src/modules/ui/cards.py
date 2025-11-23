from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt

class AnimeCard(QFrame):
    def __init__(self, anime_data, image_loader_callback):
        super().__init__()
        self.anime_data = anime_data
        self.image_loader_callback = image_loader_callback
        self.setFixedSize(200, 350)
        self.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                border: none;
            }
            QFrame:hover {
                background: #3a3a3a;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Imagem do anime
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 280)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #3a3a3a;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        
        # Texto placeholder
        self.image_label.setText("📺\nCarregando...")
        self.image_label.setStyleSheet(self.image_label.styleSheet() + """
            QLabel {
                color: #888;
                font-size: 12px;
            }
        """)

        # Informações do anime
        info_widget = QWidget()
        info_widget.setStyleSheet("""
            background: #2a2a2a; 
            border-bottom-left-radius: 10px; 
            border-bottom-right-radius: 10px;
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(5)

        # Título
        title = QLabel(self.anime_data["title"])
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #fff;
                line-height: 1.3;
            }
        """)
        title.setWordWrap(True)
        title.setFixedHeight(40)

        # Detalhes
        details = QLabel(f"Rank: #{self.anime_data['score']}")
        details.setStyleSheet("font-size: 12px; color: #ccc;")

        # Status
        status = QLabel("Popular")
        status.setStyleSheet("""
            QLabel {
                background: #ff7b00;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                max-width: 80px;
            }
        """)

        info_layout.addWidget(title)
        info_layout.addWidget(details)
        info_layout.addWidget(status)
        info_widget.setLayout(info_layout)

        layout.addWidget(self.image_label)
        layout.addWidget(info_widget)
        self.setLayout(layout)
        
        # Carregar imagem
        self.load_image()
    
    def load_image(self):
        """Inicia o carregamento da imagem"""
        poster_url = self.anime_data.get("poster", "")
        if poster_url:
            self.image_loader_callback(
                self.anime_data["id"], 
                poster_url, 
                self.image_label
            )
        else:
            self.image_label.setText("🎬\nSem imagem")
            self.image_label.setStyleSheet(self.image_label.styleSheet() + """
                QLabel {
                    color: #666;
                    font-size: 12px;
                }
            """)