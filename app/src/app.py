import sqlite3
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt
from loguru import logger
import jwt
import datetime

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

        #usuario/autenticacao
        self.auth_system = AuthSystem()
        self.current_user = None
        self.user_db = None

        self.init_ui()

        self.try_auto_login()

        #inicia a API do Aniwatch
        self.init_aniwatch_api()

    def try_auto_login(self):
        try:
            session_payload = self.auth_system.load_session()
            if session_payload and 'user_id' in session_payload:
                user_id = session_payload['user_id']
                logger.info(f"🎯 Tentando login automático para usuário ID: {user_id}")
                
                new_token = jwt.encode({
                    'user_id': session_payload['user_id'],
                    'username': session_payload['username'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
                }, self.auth_system.secret_key, algorithm='HS256')
                
                self.on_login_success(new_token, auto_login=True)
            else:
                logger.info("ℹ️ Nenhuma sessão válida encontrada para auto-login")
                
        except Exception as e:
            logger.error(f"❌ Erro no auto-login: {e}")
            self.auth_system.clear_session()
    
    def on_login_success(self, token, auto_login=False):
        """Chamado quando login é bem-sucedido"""
        success, payload = self.auth_system.verify_token(token)
        if success:
            self.current_user = payload
            
            if not auto_login:
                self.auth_system.save_session(payload['user_id'], token)
            
            self.load_user_data()
            self.stacked_widget.setCurrentIndex(1)
            
            if auto_login:
                logger.info(f"⚡ Login automático bem-sucedido: {self.current_user['username']}")
            else:
                logger.info(f"✅ Login bem-sucedido: {self.current_user['username']}")
    
    def init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.auth_widget = AuthWidget(self.auth_system, self.on_login_success)
        self.stacked_widget.addWidget(self.auth_widget)
        
        self.main_widget = self.create_main_widget()
        self.stacked_widget.addWidget(self.main_widget)
        
        self.stacked_widget.setCurrentIndex(0)
    
    def create_main_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        
        #título
        title = QLabel("AniPlay - Seu Player de Anime")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f7fafc;")
        
        #botão de logout
        self.logout_btn = QPushButton("🚪 Sair")
        self.logout_btn.setFixedSize(100, 35)
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.logout_btn)
        
        #conteúdo principal
        self.welcome_label = QLabel("Bem-vindo ao AniPlay! 🎉")
        self.welcome_label.setStyleSheet("font-size: 18px; color: #e2e8f0;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.welcome_label)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def update_welcome_message(self):
        if self.current_user:
            username = self.current_user.get('username', 'Usuário')
            self.welcome_label.setText(f"Bem-vindo, {username}! 🎉")
    
    def load_user_data(self):
        try:
            user_id = self.current_user['user_id']
            user_db_path = self.auth_system.get_app_data_path() / f"user_{user_id}.db"
            
            self.user_db = sqlite3.connect(user_db_path)
            
            cursor = self.user_db.cursor()
            cursor.execute("SELECT theme, language FROM preferences WHERE user_id = ?", (user_id,))
            prefs = cursor.fetchone()
            
            if prefs:
                theme, language = prefs
                logger.info(f"🎨 Preferências carregadas: {theme}, {language}")
            
            self.update_welcome_message()
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados do usuário: {e}")
    
    def logout(self):
        reply = QMessageBox.question(
            self, 
            "Sair", 
            "Deseja realmente sair?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_system.clear_session()
            
            self.current_user = None
            if self.user_db:
                self.user_db.close()
                self.user_db = None
            
            self.stacked_widget.setCurrentIndex(0)
            logger.info("👋 Usuário fez logout")
    
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
