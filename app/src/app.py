import sys
import subprocess
from pathlib import Path
import threading
import sqlite3
import datetime

from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
                                QLabel, QPushButton, QHBoxLayout, QMessageBox, QFrame,
                                QLineEdit, QListWidget, QScrollArea, QDialog)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThreadPool
from PySide6.QtGui import QPixmap
from loguru import logger
import jwt

from api.server_monitor import ServerMonitor
from image_loader import ImageLoader

from modules.ui.header import HeaderWidget
from modules.cache.image_cache import ImageCacheManager
from modules.ui.cards import AnimeCard
from modules.auth.auth import AuthSystem
from modules.auth.auth_widget import AuthWidget
from modules.ui.home import Home



class AniPlayApp(QMainWindow):
    api_ready_signal = Signal(bool)

    def __init__(self):
        super().__init__()
        # Configura a janela principal
        self.setWindowTitle("AniPlay")
        self.resize(1200, 800)

        # Inicia o logger
        self.setup_logger()
        logger.info("AniPlay iniciado")

        # Usuario/autenticacao
        self.auth_system = AuthSystem()
        self.current_user = None
        self.user_db = None

        # Inicializar módulos
        self.cache_manager = ImageCacheManager(self.auth_system)
        
        # Thread pool para carregamento de imagens
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(3)

        self.init_ui()
        self.try_auto_login()

        # Inicia a API do Aniwatch
        self.init_aniwatch_api()

        self.api_ready_signal.connect(self.on_api_ready)

        cache_size = self.cache_manager.get_cache_size()
        cache_files_count = self.check_cache_files()
        logger.info(f"💾 Cache local: {cache_size:.2f} MB, {cache_files_count} arquivos")

    def check_cache_files(self):
        """Verifica quantos arquivos de cache existem (para debug)"""
        try:
            cache_files = list(self.cache_manager.cache_dir.glob("*.*"))
            logger.info(f"📁 Arquivos no cache: {len(cache_files)}")
            
            # Lista os primeiros 5 arquivos para debug
            for i, file_path in enumerate(cache_files[:5]):
                file_size = file_path.stat().st_size / 1024  # KB
                logger.debug(f"  {i+1}. {file_path.name} ({file_size:.1f} KB)")
                
            return len(cache_files)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar cache: {e}")
            return 0

    def load_anime_poster_async(self, anime_id, image_url, image_label):
        """Carrega uma imagem de forma assíncrona com cache"""
        anime_id = str(anime_id).strip()
        
        # 1. Cache de memória
        if anime_id in self.cache_manager.poster_cache:
            logger.debug(f"✅ Imagem {anime_id} já em cache de memória")
            pixmap = self.cache_manager.poster_cache[anime_id]
            image_label.setPixmap(pixmap)
            image_label.setText("")
            return
        
        # 2. Cache de disco (síncrono)
        cache_pixmap = self.cache_manager.load_from_cache_sync(anime_id, image_url)
        if cache_pixmap:
            logger.debug(f"💾 Cache SÍNCRONO encontrado: {anime_id}")
            self.cache_manager.poster_cache[anime_id] = cache_pixmap
            image_label.setPixmap(cache_pixmap)
            image_label.setText("")
            return
        
        # 3. Download (assíncrono)
        if anime_id in self.cache_manager.pending_images:
            logger.debug(f"⏳ ID {anime_id} já está sendo carregado")
            return
        
        # Marca como carregando
        self.cache_manager.pending_images.add(anime_id)
        logger.debug(f"🚀 Iniciando carregamento assíncrono: {anime_id}")
        
        # Cria o worker apenas para download (não para cache)
        worker = ImageLoader(anime_id, image_url, self.cache_manager.cache_dir)
        
        # Conecta os sinais
        worker.signals.image_loaded.connect(
            lambda anime_id, pixmap: self.on_poster_loaded(anime_id, pixmap, image_label)
        )
        worker.signals.image_failed.connect(
            lambda anime_id, error: self.on_poster_failed(anime_id, error, image_label)
        )
        
        # Inicia o worker no thread pool
        self.thread_pool.start(worker)

    def on_poster_loaded(self, anime_id, pixmap, image_label):
        """Chamado quando uma imagem é carregada com sucesso"""
        # Remove da lista de pendentes
        if anime_id in self.cache_manager.pending_images:
            self.cache_manager.pending_images.remove(anime_id)
        
        # Salva no cache
        self.cache_manager.poster_cache[anime_id] = pixmap
        
        # Atualiza a UI
        image_label.setPixmap(pixmap)
        image_label.setText("")
        
        logger.debug(f"✅ Imagem {anime_id} carregada com sucesso")

    def on_poster_failed(self, anime_id, error, image_label):
        """Chamado quando falha ao carregar uma imagem"""
        # Remove da lista de pendentes
        if anime_id in self.cache_manager.pending_images:
            self.cache_manager.pending_images.remove(anime_id)
        
        logger.warning(f"❌ Falha ao carregar poster {anime_id}: {error}")
        image_label.setText("🎬\nSem imagem")
        image_label.setStyleSheet(image_label.styleSheet() + """
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)

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

        # Header modularizado
        self.header = HeaderWidget()
        self.header.login_clicked.connect(self.show_auth_modal)
        self.header.register_clicked.connect(self.show_auth_modal)
        self.header.logout_clicked.connect(self.logout)
        layout.addWidget(self.header)

        # Seção de busca
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
        """)

        # Conteúdo principal
        self.home_container = QWidget()
        self.home_layout = QVBoxLayout()
        self.home_container.setLayout(self.home_layout)

        # --- CARREGANDO (EXIBIDO ATÉ api_ready=True) ---
        self.loading_label = QLabel("Carregando")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #ff7b00;
                padding: 50px;
            }
        """)

        self.home_layout.addWidget(self.loading_label)

        # Animação dos pontinhos
        self.loading_dots = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.animate_loading)
        self.loading_timer.start(500)

        scroll.setWidget(self.home_container)
        return scroll
    
    def animate_loading(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        self.loading_label.setText("Carregando" + "." * self.loading_dots)

    def create_anime_card(self, anime):
        """Cria um card de anime usando o novo componente modular"""
        card = AnimeCard(anime, self.load_anime_poster_async)
        return card

    def create_anime_section(self, title, animes):
        section = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 20)

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

        for anime in animes[:10]:  # Limita a 10 animes por seção
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
            # Usa o método do header modularizado
            self.header.update_user_info(username)
            self.profile_tab.show()
            
            # Atualizar conteúdo do perfil
            self.update_profile_tab()

    def update_profile_tab(self):
        """Atualiza o conteúdo da aba de perfil"""
        if self.current_user:
            username = self.current_user.get('username', 'Usuário')
            email = self.current_user.get('email', 'Não informado')
            
            # Criar um novo widget para o perfil
            new_profile_widget = QWidget()
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
            new_profile_widget.setLayout(profile_layout)
            
            # Substituir o widget no content_stack
            self.content_stack.removeWidget(self.profile_content)
            self.profile_content = new_profile_widget
            self.content_stack.insertWidget(2, self.profile_content)

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
            
            # Resetar UI usando o header modularizado
            self.header.update_user_info(None)
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
        if sender == self.header.register_btn:
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
        self.server_monitor = ServerMonitor()
        self.server_monitor.wait_for_server(
            lambda ready: self.api_ready_signal.emit(ready)
        )

    @Slot(bool)
    def on_api_status_changed(self, is_ready):
        if is_ready:
            self.on_api_ready()
  
    def on_api_ready(self):
        self.cache_manager.pending_images.clear()

         # Para animação
        self.loading_timer.stop()
        self.loading_label.hide()

        home_sections = Home(self.home_layout, self.create_anime_section)

    def closeEvent(self, event):
        # Log do tamanho do cache ao fechar
        cache_size = self.cache_manager.get_cache_size()
        logger.info(f"💾 Cache final: {cache_size:.2f} MB")
        
        # Limpa o thread pool
        self.thread_pool.clear()
        self.thread_pool.waitForDone(3000)
        
        if self.user_db:
            self.user_db.close()
        event.accept()
