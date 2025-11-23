from PySide6.QtWidgets import (QMainWindow)
from loguru import logger

import threading
import sys
import subprocess
from pathlib import Path

class AniPlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        #configura a janela principal
        self.setWindowTitle("AniPlay")
        self.resize(1200, 800)

        #inicia o logger
        self.setup_logger()
        logger.info("AniPlay Application Started")

        #inicia a API do Aniwatch
        self.init_aniwatch_api()
    
    def setup_logger(self):
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        logger.add("app.log", rotation="10 MB", retention="30 days")

    def init_aniwatch_api(self):
        logger.info("Inicializando Anime API...")
        
        def start_api():
            api_path = Path(__file__).parent.parent.parent / "aniwatch-api"
            
            if api_path.exists():
                logger.info(f"Executando npm start em: {api_path}")
                # Mude para Popen e adicione thread
                subprocess.Popen(
                    "npm start", 
                    cwd=str(api_path), 
                    shell=True
                )
                logger.info("✅ Anime API iniciada em background")
            else:
                logger.error(f"Diretório não encontrado: {api_path}")
        
        import threading
        threading.Thread(target=start_api, daemon=True).start()
