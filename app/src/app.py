import sqlite3
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget)
from loguru import logger

import sys
import subprocess
from pathlib import Path

from auth.auth import AuthSystem
from auth.auth_widget import AuthWidget

class AniPlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        #configura a janela principal
        self.setWindowTitle("AniPlay")
        self.resize(1200, 800)

        #inicia o logger
        self.setup_logger()
        logger.info("AniPlay iniciado")

        #inicia a API do Aniwatch
        self.init_aniwatch_api()

        #usuario/autenticacao
        self.auth_system = AuthSystem()
        self.current_user = None
        self.user_db = None

        self.init_ui()
    
    def init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        #tela de login
        self.login_widget = AuthWidget(self.auth_system, self.on_login_success)
        self.stacked_widget.addWidget(self.login_widget)
        
        #tela principal
        self.main_widget = QWidget()
        self.stacked_widget.addWidget(self.main_widget)
        
        #mostra tela de login inicialmente
        self.stacked_widget.setCurrentIndex(0)
    
    def on_login_success(self, token):
        success, payload = self.auth_system.verify_token(token)
        if success:
            self.current_user = payload
            self.load_user_data()
            self.stacked_widget.setCurrentIndex(1)
            logger.info(f"Usuário {self.current_user['username']} logado com sucesso")
    
    def load_user_data(self):
        user_id = self.current_user['user_id']
        user_db_path = self.auth_system.get_app_data_path() / f"user_{user_id}.db"
        
        self.user_db = sqlite3.connect(user_db_path)
        
        cursor = self.user_db.cursor()
        cursor.execute("SELECT theme, language FROM preferences WHERE user_id = ?", (user_id,))
        prefs = cursor.fetchone()
        
        if prefs:
            theme, language = prefs
            logger.info(f"Preferências carregadas: {theme}, {language}")

    def setup_logger(self):
        logger.remove()

        log_file = Path("app.log")
        if log_file.exists():
            log_file.unlink()
        
        logger.add(sys.stderr, level="INFO")
        logger.add("app.log", rotation="10 MB", retention="30 days")

    def init_aniwatch_api(self):
        logger.info("Inicializando Anime API...")
        
        def start_api():
            api_path = Path(__file__).parent.parent.parent / "aniwatch-api"
            
            if api_path.exists():
                logger.info(f"Executando npm start em: {api_path}")
                subprocess.Popen(
                    "npm start", 
                    cwd=str(api_path), 
                    shell=True
                )
                logger.info("Anime API iniciada em background")
            else:
                logger.error(f"Diretório não encontrado: {api_path}")
        
        import threading
        threading.Thread(target=start_api, daemon=True).start()
    
    def closeEvent(self, event):
        if self.user_db:
            self.user_db.close()
        event.accept()
