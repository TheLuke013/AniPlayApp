import requests
import os
from pathlib import Path
from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject, Qt
from PySide6.QtGui import QPixmap
from loguru import logger

class ImageSignals(QObject):
    image_loaded = Signal(str, QPixmap)
    image_failed = Signal(str, str)

class ImageLoader(QRunnable):
    def __init__(self, anime_id, image_url, cache_dir):
        super().__init__()
        self.anime_id = anime_id
        self.image_url = image_url
        self.cache_dir = cache_dir
        self.signals = ImageSignals()
        self.setAutoDelete(True)

    def get_cache_path(self):
        """Retorna o caminho do arquivo baseado no anime_id."""
        extension = Path(self.image_url).suffix.lower()

        if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
            extension = ".jpg"

        return self.cache_dir / f"{self.anime_id}{extension}"

    def load_from_cache(self):
        cache_path = self.get_cache_path()
        if cache_path.exists():
            try:
                file_size = cache_path.stat().st_size
                if file_size < 1024:
                    logger.warning(f"🗑️ Cache muito pequeno, removendo: {cache_path}")
                    cache_path.unlink()
                    return None
                    
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    logger.debug(f"✅ Cache válido: {cache_path.name}, tamanho: {pixmap.width()}x{pixmap.height()}")
                    return scaled_pixmap
                else:
                    logger.warning(f"❌ Cache corrompido (pixmap isNull): {cache_path}")
                    cache_path.unlink()
            except Exception as e:
                logger.warning(f"❌ Erro ao carregar cache {cache_path}: {e}")
                try:
                    cache_path.unlink()
                except:
                    pass
        return None

    def save_to_cache(self, image_data):
        try:
            cache_path = self.get_cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'wb') as f:
                f.write(image_data)
            logger.debug(f"💾 Imagem salva em cache: {cache_path}")
        except Exception as e:
            logger.warning(f"❌ Erro ao salvar cache {cache_path}: {e}")

    def run(self):
        cached_pixmap = self.load_from_cache()
        if cached_pixmap:
            logger.debug(f"💾 Cache HIT: {self.anime_id}")
            self.signals.image_loaded.emit(self.anime_id, cached_pixmap)
            return
        else:
            cache_path = self.get_cache_path()
            logger.debug(f"💾 Cache MISS: {self.anime_id} - {cache_path}")

        try:
            logger.debug(f"🌐 Baixando: {self.anime_id} - {self.image_url}")
            response = requests.get(self.image_url, timeout=10)
            if response.status_code == 200:
                self.save_to_cache(response.content)
                
                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    scaled_pixmap = pixmap.scaled(200, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    self.signals.image_loaded.emit(self.anime_id, scaled_pixmap)
                    logger.debug(f"✅ Imagem carregada: {self.anime_id}")
                else:
                    logger.error(f"❌ Falha ao carregar dados da imagem: {self.anime_id}")
                    self.signals.image_failed.emit(self.anime_id, "Falha ao carregar dados da imagem")
            else:
                logger.error(f"❌ HTTP {response.status_code} para {self.anime_id}")
                self.signals.image_failed.emit(self.anime_id, f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Exception para {self.anime_id}: {e}")
            self.signals.image_failed.emit(self.anime_id, str(e))