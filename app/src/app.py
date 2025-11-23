import sqlite3
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
                                QLabel, QPushButton, QHBoxLayout, QMessageBox, QFrame,
                                QLineEdit, QListWidget, QScrollArea, QDialog)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThreadPool, QRunnable
import concurrent.futures
from PySide6.QtGui import QPixmap
from loguru import logger
import jwt
import datetime
import requests

import sys
import subprocess
from pathlib import Path
import threading
import json
import hashlib
from pathlib import Path

from auth.auth import AuthSystem
from auth.auth_widget import AuthWidget
from anime.anime_data import get_animes_home_page, get_search_anime
from api.server_monitor import ServerMonitor
from image_loader import ImageLoader

class AniPlayApp(QMainWindow):
    api_ready_signal = Signal(bool)

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

        self.api_ready_signal.connect(self.on_api_ready)

        self.cache_dir = self.get_cache_directory()
    
        # 🔥 CORREÇÃO: Limpar completamente os caches em memória
        self.poster_cache = {}
        self.pending_images = set()
        
        # 🔥 CORREÇÃO: Verificar e limpar cache corrompido na inicialização
        self.clean_corrupted_cache()
        
        # Thread pool para carregamento de imagens
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(3)
        
        self.poster_cache = {}
        self.pending_images = set()

        cache_size = self.get_cache_size()
        cache_files_count = self.check_cache_files()
        logger.info(f"💾 Cache local: {cache_size:.2f} MB, {cache_files_count} arquivos")

    def clean_corrupted_cache(self):
        """Remove arquivos de cache corrompidos na inicialização"""
        try:
            for cache_file in self.cache_dir.glob("*.*"):
                if cache_file.is_file():
                    # Tenta carregar como QPixmap para verificar integridade
                    pixmap = QPixmap(str(cache_file))
                    if pixmap.isNull():
                        logger.warning(f"🗑️ Removendo cache corrompido: {cache_file.name}")
                        cache_file.unlink()
        except Exception as e:
            logger.warning(f"❌ Erro ao limpar cache corrompido: {e}")

    def check_cache_files(self):
        """Verifica quantos arquivos de cache existem (para debug)"""
        try:
            cache_files = list(self.cache_dir.glob("*.*"))
            logger.info(f"📁 Arquivos no cache: {len(cache_files)}")
            
            # Lista os primeiros 5 arquivos para debug
            for i, file_path in enumerate(cache_files[:5]):
                file_size = file_path.stat().st_size / 1024  # KB
                logger.debug(f"  {i+1}. {file_path.name} ({file_size:.1f} KB)")
                
            return len(cache_files)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar cache: {e}")
            return 0

    def get_cache_directory(self):
        """Retorna o diretório de cache da aplicação (mesmo do banco de dados)"""
        # Usa o mesmo diretório base do sistema de auth
        app_data = self.auth_system.get_app_data_path()
        cache_path = app_data / "cache" / "images"
        
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"✅ Cache directory: {cache_path}")
            return cache_path
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório de cache {cache_path}: {e}")
            # Fallback para o diretório do app
            fallback_path = app_data / "images_cache"
            fallback_path.mkdir(parents=True, exist_ok=True)
            return fallback_path

    def clear_old_cache(self, days_old=30):
        """Limpa cache antigo (opcional)"""
        try:
            current_time = datetime.datetime.now().timestamp()
            for file_path in self.cache_dir.glob("*.*"):
                if file_path.is_file():
                    # Verifica se o arquivo é mais antigo que days_old
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > days_old * 24 * 60 * 60:  # Converter dias para segundos
                        file_path.unlink()
                        logger.debug(f"🗑️ Cache antigo removido: {file_path}")
        except Exception as e:
            logger.warning(f"❌ Erro ao limpar cache: {e}")

    def get_cache_size(self):
        """Retorna o tamanho total do cache em MB"""
        try:
            total_size = 0
            for file_path in self.cache_dir.glob("*.*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # Converter para MB
        except Exception as e:
            logger.warning(f"❌ Erro ao calcular tamanho do cache: {e}")
            return 0

    def load_anime_poster_async(self, anime_id, image_url, image_label):
        anime_id = str(anime_id).strip()
        
        # Verifica se já está no cache de memória
        if anime_id in self.poster_cache:
            logger.debug(f"✅ Imagem {anime_id} já em cache de memória")
            pixmap = self.poster_cache[anime_id]
            image_label.setPixmap(pixmap)
            image_label.setText("")
            return
        
        # 🔥 CORREÇÃO: Verificar cache de disco de forma SÍNCRONA primeiro
        cache_pixmap = self.load_from_cache_sync(anime_id, image_url)
        if cache_pixmap:
            logger.debug(f"💾 Cache SÍNCRONO encontrado: {anime_id}")
            self.poster_cache[anime_id] = cache_pixmap
            image_label.setPixmap(cache_pixmap)
            image_label.setText("")
            return
        
        # Se já está carregando, apenas retorna
        if anime_id in self.pending_images:
            logger.debug(f"⏳ ID {anime_id} já está sendo carregado")
            return
        
        # Marca como carregando
        self.pending_images.add(anime_id)
        logger.debug(f"🚀 Iniciando carregamento assíncrono: {anime_id}")
        
        # Cria o worker apenas para download (não para cache)
        worker = ImageLoader(anime_id, image_url, self.cache_dir)
        
        # Conecta os sinais
        worker.signals.image_loaded.connect(
            lambda anime_id, pixmap: self.on_poster_loaded(anime_id, pixmap, image_label)
        )
        worker.signals.image_failed.connect(
            lambda anime_id, error: self.on_poster_failed(anime_id, error, image_label)
        )
        
        # Inicia o worker no thread pool
        self.thread_pool.start(worker)

    def load_from_cache_sync(self, anime_id, image_url):
        """Verifica o cache de disco de forma síncrona"""
        try:
            # Recria a lógica do ImageLoader.get_cache_path()
            extension = Path(image_url).suffix.lower()
            if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
                extension = ".jpg"
            
            cache_path = self.cache_dir / f"{anime_id}{extension}"
            
            if cache_path.exists():
                # Verifica se o arquivo tem tamanho válido
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

    def on_poster_loaded(self, anime_id, pixmap, image_label):
        """Chamado quando uma imagem é carregada com sucesso"""
        # 🔥 CORREÇÃO: Verificar se estamos na thread principal
        from PySide6.QtCore import QThread
        logger.debug(f"🎯 Thread atual: {QThread.currentThread()}")
        
        # Remove da lista de pendentes
        if anime_id in self.pending_images:
            self.pending_images.remove(anime_id)
        
        # Salva no cache
        self.poster_cache[anime_id] = pixmap
        
        # Atualiza a UI
        image_label.setPixmap(pixmap)
        image_label.setText("")
        
        logger.debug(f"✅ Imagem {anime_id} carregada com sucesso")

    def on_poster_failed(self, anime_id, error, image_label):
        """Chamado quando falha ao carregar uma imagem"""
        logger.debug(f"🎯 on_poster_failed chamado para: {anime_id}")
        
        # Remove da lista de pendentes
        if anime_id in self.pending_images:
            self.pending_images.remove(anime_id)
        
        logger.warning(f"❌ Falha ao carregar poster {anime_id}: {error}")
        image_label.setText("🎬\nSem imagem")
        image_label.setStyleSheet(image_label.styleSheet() + """
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)
    def retry_loading(self, anime_id, image_label):
        """Tenta recarregar uma imagem que falhou"""
        # Busca os dados do anime novamente (você precisará armazenar a URL)
        if hasattr(self, 'current_anime_data'):
            for anime in self.current_anime_data:
                if str(anime["id"]) == anime_id:
                    self.load_anime_poster_async(anime_id, anime.get("poster", ""), image_label)
                    break

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

        # Imagem do anime
        image_label = QLabel()
        image_label.setFixedSize(200, 280)
        image_label.setStyleSheet("""
            QLabel {
                background: #3a3a3a;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }
        """)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setScaledContents(False)  # IMPORTANTE: não escalar, pois já fazemos isso no loader
        
        # Texto placeholder enquanto a imagem carrega
        image_label.setText("📺\nCarregando...")
        image_label.setStyleSheet(image_label.styleSheet() + """
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
        details = QLabel(f"Rank: #{anime['score']}")
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

        layout.addWidget(image_label)
        layout.addWidget(info_widget)
        card.setLayout(layout)

        # Iniciar carregamento assíncrono da imagem
        poster_url = anime.get("poster", "")
        if poster_url:
            self.load_anime_poster_async(anime["id"], poster_url, image_label)
        else:
            image_label.setText("🎬\nSem imagem")
            image_label.setStyleSheet(image_label.styleSheet() + """
                QLabel {
                    color: #666;
                    font-size: 12px;
                }
            """)

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
            
            # 🔥 CORREÇÃO: Criar um novo widget para o perfil
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
            
            # 🔥 CORREÇÃO: Substituir o widget no content_stack
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
        self.server_monitor = ServerMonitor()
        self.server_monitor.wait_for_server(
            lambda ready: self.api_ready_signal.emit(ready)
        )

    @Slot(bool)
    def on_api_status_changed(self, is_ready):
        if is_ready:
            self.on_api_ready()
  
    def on_api_ready(self):
        self.pending_images.clear()

        home_animes_data = get_animes_home_page()
        trending_animes = home_animes_data["data"]["trendingAnimes"]
        popular_animes = home_animes_data["data"]["mostPopularAnimes"]
        recent_animes = home_animes_data["data"]["latestCompletedAnimes"]
        
        logger.info("✅ Dados dos animes obtidos com sucesso")

        # Para animação
        self.loading_timer.stop()
        self.loading_label.hide()

        # Limpa o layout antes de adicionar novas seções
        for i in reversed(range(self.home_layout.count())):
            widget = self.home_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Converte os dados para o formato esperado pelo create_anime_section
        def convert_anime_data(anime_list):
            converted = []
            for anime in anime_list:
                converted.append({
                    "title": anime.get("name", "Sem título"),
                    "score": str(anime.get("rank", "N/A")),
                    "status": "Em andamento",  # Você pode ajustar isso conforme os dados reais
                    "poster": anime.get("poster", ""),
                    "id": anime.get("id", "")
                })
            return converted

        # Adiciona as seções com dados reais
        trending_section = self.create_anime_section("🔥 Em Alta Agora", convert_anime_data(trending_animes))
        popular_section = self.create_anime_section("⭐ Clássicos Populares", convert_anime_data(popular_animes))
        recent_section = self.create_anime_section("🆕 Lançamentos Recentes", convert_anime_data(recent_animes))

        self.home_layout.addWidget(trending_section)
        self.home_layout.addWidget(popular_section)
        self.home_layout.addWidget(recent_section)

    def closeEvent(self, event):
        # Log do tamanho do cache ao fechar
        cache_size = self.get_cache_size()
        logger.info(f"💾 Cache final: {cache_size:.2f} MB")
        
        # Limpa o thread pool
        self.thread_pool.clear()
        self.thread_pool.waitForDone(3000)
        
        if self.user_db:
            self.user_db.close()
        event.accept()