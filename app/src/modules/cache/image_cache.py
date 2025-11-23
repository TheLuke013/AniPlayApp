import datetime
from pathlib import Path
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from loguru import logger

class ImageCacheManager:
    def __init__(self, auth_system):
        self.auth_system = auth_system
        self.cache_dir = self.get_cache_directory()
        self.poster_cache = {}
        self.pending_images = set()
        
    def get_cache_directory(self):
        """Retorna o diretório de cache da aplicação"""
        app_data = self.auth_system.get_app_data_path()
        cache_path = app_data / "cache" / "images"
        
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"✅ Cache directory: {cache_path}")
            return cache_path
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório de cache: {e}")
            fallback_path = app_data / "images_cache"
            fallback_path.mkdir(parents=True, exist_ok=True)
            return fallback_path
    
    def load_from_cache_sync(self, anime_id, image_url):
        """Verifica o cache de disco de forma síncrona"""
        try:
            extension = Path(image_url).suffix.lower()
            if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
                extension = ".jpg"
            
            cache_path = self.cache_dir / f"{anime_id}{extension}"
            
            if cache_path.exists():
                file_size = cache_path.stat().st_size
                if file_size < 1024:
                    cache_path.unlink()
                    return None
                    
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    logger.debug(f"✅ Cache síncrono válido: {cache_path.name}")
                    return scaled_pixmap
                else:
                    cache_path.unlink()
        except Exception as e:
            logger.warning(f"❌ Erro ao carregar cache síncrono: {e}")
        
        return None
    
    def clean_corrupted_cache(self):
        """Remove arquivos de cache corrompidos"""
        try:
            for cache_file in self.cache_dir.glob("*.*"):
                if cache_file.is_file():
                    pixmap = QPixmap(str(cache_file))
                    if pixmap.isNull():
                        logger.warning(f"🗑️ Removendo cache corrompido: {cache_file.name}")
                        cache_file.unlink()
        except Exception as e:
            logger.warning(f"❌ Erro ao limpar cache corrompido: {e}")
    
    def get_cache_size(self):
        """Retorna o tamanho total do cache em MB"""
        try:
            total_size = 0
            for file_path in self.cache_dir.glob("*.*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)
        except Exception as e:
            logger.warning(f"❌ Erro ao calcular tamanho do cache: {e}")
            return 0