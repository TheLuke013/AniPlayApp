import requests
from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject, Qt
from PySide6.QtGui import QPixmap
from loguru import logger

class ImageSignals(QObject):
    image_loaded = Signal(str, QPixmap)  # anime_id, pixmap
    image_failed = Signal(str, str)      # anime_id, error_message

class ImageLoader(QRunnable):
    def __init__(self, anime_id, image_url):
        super().__init__()
        self.anime_id = anime_id
        self.image_url = image_url
        self.signals = ImageSignals()
        self.setAutoDelete(True)  # Importante: auto-deleta após execução

    def run(self):
        try:
            response = requests.get(self.image_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    # Redimensiona a imagem para o tamanho do card
                    scaled_pixmap = pixmap.scaled(200, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    self.signals.image_loaded.emit(self.anime_id, scaled_pixmap)
                else:
                    self.signals.image_failed.emit(self.anime_id, "Falha ao carregar dados da imagem")
            else:
                self.signals.image_failed.emit(self.anime_id, f"HTTP {response.status_code}")
        except Exception as e:
            self.signals.image_failed.emit(self.anime_id, str(e))