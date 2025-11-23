import sqlite3
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
                                QLabel, QPushButton, QHBoxLayout, QMessageBox, QFrame,
                                QLineEdit, QListWidget, QScrollArea, QDialog)
from PySide6.QtCore import Qt
from loguru import logger
import jwt
import datetime

import sys
import subprocess
from pathlib import Path
import threading

from auth.auth import AuthSystem
from auth.auth_widget import AuthWidget
from anime.anime_data import get_anime_info
from api.server_monitor import ServerMonitor

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
            self.update_ui_after_login()
            
            if auto_login:
                logger.info(f"⚡ Login automático bem-sucedido: {self.current_user['username']}")
            else:
                logger.info(f"✅ Login bem-sucedido: {self.current_user['username']}")
    
    def init_ui(self):
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Seção de busca (igual ao HTML)
        search_section = self.create_search_section()
        layout.addWidget(search_section)

        # Abas
        tabs = self.create_tabs()
        layout.addWidget(tabs)

        # Conteúdo das abas
        self.content_stack = QStackedWidget()
        self.setup_tab_content()
        layout.addWidget(self.content_stack)

        main_widget.setLayout(layout)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Logo
        logo = QLabel("🎬 AniPlay")
        logo.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ff7b00;
            }
        """)

        # Área do usuário
        user_widget = QWidget()
        user_layout = QHBoxLayout()
        user_layout.setSpacing(10)

        # Mensagem de boas-vindas (inicialmente hidden)
        self.welcome_label = QLabel("Olá, <span style='color: #ff7b00; font-weight: bold;'>Usuário</span>!")
        self.welcome_label.setStyleSheet("color: #ccc;")
        self.welcome_label.hide()

        # Botões de autenticação
        self.login_btn = QPushButton("Entrar")
        self.register_btn = QPushButton("Cadastrar")
        self.logout_btn = QPushButton("Sair")
        self.logout_btn.hide()

        # Estilização dos botões (SEM transform)
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
        """

        self.login_btn.setStyleSheet(button_style + """
            QPushButton {
                background: transparent;
                color: #ff7b00;
                border: 1px solid #ff7b00;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """)

        self.register_btn.setStyleSheet(button_style + """
            QPushButton {
                background: #ff7b00;
                color: white;
            }
            QPushButton:hover {
                background: #ff9500;
            }
        """)

        self.logout_btn.setStyleSheet(button_style + """
            QPushButton {
                background: transparent;
                color: #ff7b00;
                border: 1px solid #ff7b00;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """)

        user_layout.addWidget(self.welcome_label)
        user_layout.addWidget(self.login_btn)
        user_layout.addWidget(self.register_btn)
        user_layout.addWidget(self.logout_btn)
        user_layout.addStretch()

        user_widget.setLayout(user_layout)

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(user_widget)

        header.setLayout(layout)
        
        # 🔥 CORREÇÃO: Conectar botões aos métodos corretos
        self.login_btn.clicked.connect(self.show_auth_modal)
        self.register_btn.clicked.connect(self.show_auth_modal)
        self.logout_btn.clicked.connect(self.logout)
        
        return header

    def show_auth_modal(self):
        """Mostra o modal de autenticação (login/registro)"""
        # Criar uma janela de diálogo modal
        auth_dialog = QDialog(self)
        auth_dialog.setWindowTitle("AniPlay - Autenticação")
        auth_dialog.setModal(True)
        auth_dialog.resize(400, 500)
        auth_dialog.setStyleSheet("""
            QDialog {
                background: #2a2a2a;
                border-radius: 10px;
            }
        """)
        
        # Criar o AuthWidget dentro do diálogo
        auth_widget = AuthWidget(self.auth_system, lambda token: self.on_auth_success(token, auth_dialog))
        
        # Layout para o diálogo
        layout = QVBoxLayout()
        layout.addWidget(auth_widget)
        auth_dialog.setLayout(layout)
        
        # Se o botão clicado foi "Cadastrar", já mostrar a aba de registro
        sender = self.sender()
        if sender == self.register_btn:
            auth_widget.show_register()
        else:
            auth_widget.show_login()
            
        auth_dialog.exec()

    def on_auth_success(self, token, auth_dialog):
        """Chamado quando a autenticação é bem-sucedida"""
        # Fechar o diálogo primeiro
        auth_dialog.accept()
        
        # Processar o login
        self.on_login_success(token)

    def create_search_section(self):
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Campo de busca
        search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome do anime...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
            }
        """)
        self.search_input.setMinimumWidth(400)

        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background: #ff7b00;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #ff9500;
            }
        """)

        search_layout.addStretch()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addStretch()

        search_widget.setLayout(search_layout)

        layout.addWidget(search_widget)

        section.setLayout(layout)
        return section

    def create_tabs(self):
        tabs_widget = QWidget()
        tabs_widget.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 5px;
                margin-bottom: 20px;
            }
        """)

        layout = QHBoxLayout()
        layout.setSpacing(5)

        # Criar abas
        self.home_tab = QPushButton("🏠 Início")
        self.search_tab = QPushButton("🔍 Busca")
        self.profile_tab = QPushButton("👤 Perfil")
        self.profile_tab.hide()  # Inicialmente escondido

        # Estilização das abas (SEM flex)
        tab_style = """
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                text-align: center;
                border: none;
                color: white;
                background: transparent;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """

        active_tab_style = """
            QPushButton {
                background: #ff7b00;
                color: white;
            }
        """

        self.home_tab.setStyleSheet(tab_style + active_tab_style)
        self.search_tab.setStyleSheet(tab_style)
        self.profile_tab.setStyleSheet(tab_style)

        # Conectar clicks
        self.home_tab.clicked.connect(lambda: self.show_tab('home'))
        self.search_tab.clicked.connect(lambda: self.show_tab('search'))
        self.profile_tab.clicked.connect(lambda: self.show_tab('profile'))

        layout.addWidget(self.home_tab)
        layout.addWidget(self.search_tab)
        layout.addWidget(self.profile_tab)

        tabs_widget.setLayout(layout)
        return tabs_widget

    def setup_tab_content(self):
        # Tela Início
        self.home_content = self.create_home_tab()
        self.content_stack.addWidget(self.home_content)

        # Tela Busca
        self.search_content = self.create_search_tab()
        self.content_stack.addWidget(self.search_content)

        # Tela Perfil
        self.profile_content = self.create_profile_tab()
        self.content_stack.addWidget(self.profile_content)

        # Mostrar tela inicial
        self.content_stack.setCurrentIndex(0)

    def create_home_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ff7b00;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff9500;
            }
        """)

        content = QWidget()
        layout = QVBoxLayout()

        # Seção "Em Alta Agora"
        trending_section = self.create_anime_section("🔥 Em Alta Agora", [
            {"title": "Attack on Titan", "score": "9.8", "status": "Em exibição"},
            {"title": "Demon Slayer", "score": "9.5", "status": "Concluído"},
            {"title": "Jujutsu Kaisen", "score": "9.3", "status": "Em exibição"},
            {"title": "One Piece", "score": "9.7", "status": "Em exibição"},
            {"title": "My Hero Academia", "score": "9.2", "status": "Em exibição"},
        ])

        # Seção "Clássicos Populares"
        popular_section = self.create_anime_section("⭐ Clássicos Populares", [
            {"title": "Naruto Shippuden", "score": "9.6", "status": "Concluído"},
            {"title": "Death Note", "score": "9.4", "status": "Concluído"},
            {"title": "Fullmetal Alchemist", "score": "9.7", "status": "Concluído"},
            {"title": "Dragon Ball Z", "score": "9.1", "status": "Concluído"},
            {"title": "Hunter x Hunter", "score": "9.5", "status": "Concluído"},
        ])

        # Seção "Lançamentos Recentes"
        recent_section = self.create_anime_section("🆕 Lançamentos Recentes", [
            {"title": "Chainsaw Man", "score": "9.4", "status": "Novo"},
            {"title": "Spy x Family", "score": "9.2", "status": "Novo"},
            {"title": "Blue Lock", "score": "9.1", "status": "Novo"},
            {"title": "Oshi no Ko", "score": "9.3", "status": "Novo"},
            {"title": "Hell's Paradise", "score": "9.0", "status": "Novo"},
        ])

        layout.addWidget(trending_section)
        layout.addWidget(popular_section)
        layout.addWidget(recent_section)
        layout.addStretch()

        content.setLayout(layout)
        scroll.setWidget(content)
        return scroll

    def create_anime_section(self, title, animes):
        section = QWidget()
        layout = QVBoxLayout()

        # Título da seção
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                margin-bottom: 20px;
                color: #ff7b00;
                border-left: 4px solid #ff7b00;
                padding-left: 15px;
            }
        """)

        # Grid de animes
        grid_widget = QWidget()
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        for anime in animes:
            card = self.create_anime_card(anime)
            grid_layout.addWidget(card)

        grid_widget.setLayout(grid_layout)

        # Scroll horizontal para o grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(grid_widget)
        scroll.setFixedHeight(370)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:horizontal {
                background: #2a2a2a;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #ff7b00;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #ff9500;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(scroll)
        section.setLayout(layout)
        return section

    def create_anime_card(self, anime):
        card = QFrame()
        card.setFixedSize(200, 350)
        card.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                border: none;
            }
            QFrame:hover {
                background: #3a3a3a;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Imagem do anime (placeholder)
        image_label = QLabel()
        image_label.setFixedSize(200, 280)
        image_label.setStyleSheet("""
            QLabel {
                background: #3a3a3a;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 40px;
            }
        """)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setText("🎬")

        # Informações do anime
        info_widget = QWidget()
        info_widget.setStyleSheet("background: #2a2a2a;")
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 15, 15, 15)

        # Título
        title = QLabel(anime["title"])
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
        details = QLabel(f"Score: {anime['score']}")
        details.setStyleSheet("font-size: 12px; color: #ccc;")

        # Status
        status = QLabel(anime["status"])
        status.setStyleSheet("""
            QLabel {
                background: #00a8ff;
                color: white;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 10px;
                max-width: 80px;
            }
        """)

        info_layout.addWidget(title)
        info_layout.addWidget(details)
        info_layout.addWidget(status)
        info_widget.setLayout(info_layout)

        layout.addWidget(image_label)
        layout.addWidget(info_widget)
        card.setLayout(layout)

        return card

    def create_search_tab(self):
        content = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        message = QLabel("🔍 Digite algo na busca para encontrar animes")
        message.setStyleSheet("""
            QLabel {
                text-align: center;
                color: #888;
                padding: 40px;
                font-size: 16px;
            }
        """)

        layout.addWidget(message)
        content.setLayout(layout)
        return content

    def create_profile_tab(self):
        content = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        message = QLabel("Faça login para ver seu perfil")
        message.setStyleSheet("""
            QLabel {
                text-align: center;
                padding: 40px;
                color: #ff7b00;
                font-size: 18px;
            }
        """)

        layout.addWidget(message)
        content.setLayout(layout)
        return content

    def show_tab(self, tab_name):
        if tab_name == 'home':
            self.content_stack.setCurrentIndex(0)
            self.home_tab.setStyleSheet(self.get_tab_style(True))
            self.search_tab.setStyleSheet(self.get_tab_style(False))
            self.profile_tab.setStyleSheet(self.get_tab_style(False))
        elif tab_name == 'search':
            self.content_stack.setCurrentIndex(1)
            self.home_tab.setStyleSheet(self.get_tab_style(False))
            self.search_tab.setStyleSheet(self.get_tab_style(True))
            self.profile_tab.setStyleSheet(self.get_tab_style(False))
        elif tab_name == 'profile':
            self.content_stack.setCurrentIndex(2)
            self.home_tab.setStyleSheet(self.get_tab_style(False))
            self.search_tab.setStyleSheet(self.get_tab_style(False))
            self.profile_tab.setStyleSheet(self.get_tab_style(True))

    def get_tab_style(self, active):
        base_style = """
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                text-align: center;
                border: none;
                color: white;
                background: transparent;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """
        active_style = """
            QPushButton {
                background: #ff7b00;
                color: white;
            }
        """
        return base_style + (active_style if active else "")

    def update_ui_after_login(self):
        """Atualiza a UI após o login bem-sucedido"""
        if self.current_user:
            username = self.current_user.get('username', 'Usuário')
            self.welcome_label.setText(f"Olá, <span style='color: #ff7b00; font-weight: bold;'>{username}</span>!")
            self.welcome_label.show()
            self.login_btn.hide()
            self.register_btn.hide()
            self.logout_btn.show()
            self.profile_tab.show()
            
            # Atualizar conteúdo do perfil
            self.update_profile_tab()

    def update_profile_tab(self):
        """Atualiza o conteúdo da aba de perfil"""
        if self.current_user:
            username = self.current_user.get('username', 'Usuário')
            email = self.current_user.get('email', 'Não informado')
            
            # Criar conteúdo personalizado do perfil
            profile_layout = QVBoxLayout()
            profile_layout.setAlignment(Qt.AlignTop)
            
            # Informações do usuário
            user_info = QLabel(f"""
                <h2 style="color: #ff7b00;">👤 Meu Perfil</h2>
                <p><strong>Usuário:</strong> {username}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Membro desde:</strong> {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
            """)
            user_info.setStyleSheet("color: white; font-size: 14px;")
            
            profile_layout.addWidget(user_info)
            profile_layout.addSpacing(20)
            
            # Limpar layout atual e adicionar o novo
            if self.profile_content.layout():
                # Limpar widgets antigos
                for i in reversed(range(self.profile_content.layout().count())): 
                    self.profile_content.layout().itemAt(i).widget().setParent(None)
            
            self.profile_content.setLayout(profile_layout)

    def logout(self):
        """Faz logout do usuário"""
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
            
            # Resetar UI
            self.welcome_label.hide()
            self.login_btn.show()
            self.register_btn.show()
            self.logout_btn.hide()
            self.profile_tab.hide()
            
            # Resetar conteúdo do perfil
            self.reset_profile_tab()
            
            self.show_tab('home')
            logger.info("👋 Usuário fez logout")
    
    def reset_profile_tab(self):
        """Reseta o conteúdo da aba de perfil para o estado inicial"""
        # Limpar layout atual
        if self.profile_content.layout():
            for i in reversed(range(self.profile_content.layout().count())): 
                self.profile_content.layout().itemAt(i).widget().setParent(None)
        
        # Recriar conteúdo inicial
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        message = QLabel("Faça login para ver seu perfil")
        message.setStyleSheet("""
            QLabel {
                text-align: center;
                padding: 40px;
                color: #ff7b00;
                font-size: 18px;
            }
        """)

        layout.addWidget(message)
        self.profile_content.setLayout(layout)
    
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
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados do usuário: {e}")

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
                self.api_process = subprocess.Popen(
                    "npm start", 
                    cwd=str(api_path), 
                    shell=True
                )
                logger.info("🚀 Processo da API iniciado")
                
                self.start_api_monitoring()
            else:
                logger.error(f"❌ Diretório não encontrado: {api_path}")
        
        threading.Thread(target=start_api, daemon=True).start()

    def start_api_monitoring(self):
        monitor = ServerMonitor()
        monitor.wait_for_server(callback=self.on_api_status_changed)

    def on_api_status_changed(self, is_ready):
        if is_ready:
            logger.info("🎉 API está pronta! Habilitando funcionalidades...")
            self.api_ready = True
        else:
            logger.error("💥 API não ficou pronta a tempo")
            self.api_ready = False
    
    def closeEvent(self, event):
        if self.user_db:
            self.user_db.close()
        event.accept()