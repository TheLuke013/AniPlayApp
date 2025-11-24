from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QWidget, QFrame, QButtonGroup,
                               QRadioButton, QScrollArea)
from PySide6.QtCore import Qt
from loguru import logger

class ServerSelectionDialog(QDialog):
    def __init__(self, episode_data, servers_data, parent=None):
        super().__init__(parent)
        self.episode_data = episode_data
        self.servers_data = servers_data
        self.selected_server = None
        self.selected_language = None
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Selecionar Servidor")
        self.setFixedSize(500, 500)  # Ajustei a altura
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                border-radius: 15px;
                border: 2px solid #ff7b00;
            }
        """)
        
        # Layout principal com scroll
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #ff7b00;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        # Widget de conteúdo
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)
        
        # Título
        title_label = QLabel("🎬 Selecionar Servidor")
        title_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 22px;
                font-weight: bold;
                text-align: center;
                padding: 5px;
            }
        """)
        
        # Informações do episódio
        episode_info = self.create_episode_info()
        
        # Seção de idioma
        language_section = self.create_language_section()
        
        # Seção de servidores
        servers_section = self.create_servers_section()
        
        # Botões de ação
        buttons_section = self.create_action_buttons()
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(episode_info)
        content_layout.addWidget(language_section)
        content_layout.addWidget(servers_section)
        content_layout.addStretch()
        content_layout.addWidget(buttons_section)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
        # Configura estado inicial
        self.update_ui_state()
    
    def create_episode_info(self):
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #444;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        episode_number = self.episode_data.get('number', 'N/A')
        episode_title = self.episode_data.get('title', f'Episódio {episode_number}')
        
        # Número do episódio
        number_label = QLabel(f"Episódio {episode_number}")
        number_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Título do episódio
        title_label = QLabel(episode_title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        title_label.setWordWrap(True)
        
        layout.addWidget(number_label)
        layout.addWidget(title_label)
        widget.setLayout(layout)
        return widget
    
    def create_language_section(self):
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #444;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Título da seção
        title_label = QLabel("🌐 Escolha o Idioma")
        title_label.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Container para os botões de idioma
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Grupo de botões para idioma
        self.language_group = QButtonGroup(self)
        
        # Botão Legendado
        self.sub_btn = self.create_language_button("Legendado", "sub")
        
        # Botão Dublado
        self.dub_btn = self.create_language_button("Dublado", "dub")
        
        buttons_layout.addWidget(self.sub_btn)
        buttons_layout.addWidget(self.dub_btn)
        buttons_layout.addStretch()
        
        buttons_container.setLayout(buttons_layout)
        
        layout.addWidget(title_label)
        layout.addWidget(buttons_container)
        widget.setLayout(layout)
        return widget
    
    def create_language_button(self, text, language_type):
        """Cria um botão de seleção de idioma"""
        button = QRadioButton(text)
        button.setProperty("languageType", language_type)
        button.setFixedHeight(45)
        button.setStyleSheet("""
            QRadioButton {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 20px;
                background: #333333;
                border: 2px solid #444;
                border-radius: 8px;
            }
            QRadioButton:hover {
                background: #3a3a3a;
                border: 2px solid #666;
            }
            QRadioButton:checked {
                background: #ff7b00;
                border: 2px solid #ff9500;
                color: white;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
        """)
        
        button.toggled.connect(self.on_language_changed)
        self.language_group.addButton(button)
        
        return button
    
    def create_servers_section(self):
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #444;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Título da seção
        self.servers_title = QLabel("📡 Servidores Disponíveis")
        self.servers_title.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Container para os servidores
        self.servers_container = QWidget()
        self.servers_layout = QVBoxLayout()
        self.servers_layout.setSpacing(8)
        self.servers_layout.setContentsMargins(0, 0, 0, 0)
        
        self.servers_container.setLayout(self.servers_layout)
        
        # Mensagem quando não há servidores
        self.no_servers_label = QLabel("Selecione um idioma primeiro")
        self.no_servers_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                text-align: center;
                padding: 30px;
                background: #252525;
                border-radius: 8px;
                border: 1px dashed #444;
            }
        """)
        self.no_servers_label.setAlignment(Qt.AlignCenter)
        self.no_servers_label.setMinimumHeight(80)
        
        layout.addWidget(self.servers_title)
        layout.addWidget(self.no_servers_label)
        layout.addWidget(self.servers_container)
        
        widget.setLayout(layout)
        return widget
    
    def create_action_buttons(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Botão Cancelar
        cancel_btn = QPushButton("✕ Cancelar")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff4444;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Botão Assistir
        self.watch_btn = QPushButton("🎬 Assistir Agora")
        self.watch_btn.setFixedHeight(45)
        self.watch_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background: #ff7b00;
                color: white;
            }
            QPushButton:hover:enabled {
                background: #ff9500;
            }
        """)
        self.watch_btn.clicked.connect(self.accept)
        self.watch_btn.setEnabled(False)
        
        layout.addWidget(cancel_btn)
        layout.addWidget(self.watch_btn)
        
        widget.setLayout(layout)
        return widget
    
    def update_ui_state(self):
        """Atualiza o estado inicial da UI"""
        # Verifica quais idiomas estão disponíveis
        has_sub = bool(self.servers_data.get("sub"))
        has_dub = bool(self.servers_data.get("dub"))
        
        # Atualiza disponibilidade dos botões
        self.sub_btn.setEnabled(has_sub)
        self.dub_btn.setEnabled(has_dub)
        
        # Tooltips informativos
        if not has_sub:
            self.sub_btn.setToolTip("Legendado não disponível")
        if not has_dub:
            self.dub_btn.setToolTip("Dublado não disponível")
        
        # Seleciona automaticamente o primeiro idioma disponível
        if has_sub:
            self.sub_btn.setChecked(True)
        elif has_dub:
            self.dub_btn.setChecked(True)
        
        self.update_servers_section()
    
    def on_language_changed(self):
        """Quando o idioma é alterado"""
        self.update_servers_section()
    
    def update_servers_section(self):
        """Atualiza a seção de servidores baseado no idioma selecionado"""
        # Limpa servidores anteriores
        for i in reversed(range(self.servers_layout.count())): 
            widget = self.servers_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Esconde o container de servidores por padrão
        self.servers_container.hide()
        self.no_servers_label.show()
        
        # Determina qual idioma está selecionado
        language = None
        servers = []
        
        if self.sub_btn.isChecked() and self.sub_btn.isEnabled():
            language = "sub"
            servers = self.servers_data.get("sub", [])
            self.servers_title.setText("📡 Servidores Legendados")
        elif self.dub_btn.isChecked() and self.dub_btn.isEnabled():
            language = "dub"
            servers = self.servers_data.get("dub", [])
            self.servers_title.setText("📡 Servidores Dublados")
        else:
            # Nenhum idioma selecionado ou disponível
            self.no_servers_label.setText("Selecione um idioma primeiro")
            self.watch_btn.setEnabled(False)
            return
        
        # Verifica se há servidores disponíveis
        if not servers:
            self.no_servers_label.setText("Nenhum servidor disponível para este idioma")
            self.watch_btn.setEnabled(False)
            return
        
        # Esconde a mensagem e mostra os servidores
        self.no_servers_label.hide()
        self.servers_container.show()
        
        # Cria botões para cada servidor
        self.servers_group = QButtonGroup(self)
        
        for server in servers:
            server_btn = self.create_server_button(server, language)
            self.servers_group.addButton(server_btn)
            self.servers_layout.addWidget(server_btn)
        
        # Seleciona o primeiro servidor automaticamente
        if self.servers_group.buttons():
            self.servers_group.buttons()[0].setChecked(True)
            self.watch_btn.setEnabled(True)
    
    def create_server_button(self, server, language):
        """Cria um botão de servidor"""
        server_btn = QRadioButton(server.get('serverName', 'Servidor'))
        server_btn.setProperty("serverData", server)
        server_btn.setProperty("language", language)
        server_btn.setFixedHeight(50)
        server_btn.setStyleSheet("""
            QRadioButton {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                background: #333333;
                border: 2px solid #444;
                border-radius: 8px;
                text-align: left;
            }
            QRadioButton:hover {
                background: #3a3a3a;
                border: 2px solid #666;
            }
            QRadioButton:checked {
                background: #ff7b00;
                border: 2px solid #ff9500;
                color: white;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                margin-right: 10px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #666;
                border-radius: 8px;
                background: #2a2a2a;
            }
            QRadioButton::indicator:checked {
                border: 2px solid white;
                border-radius: 8px;
                background: white;
            }
        """)
        
        server_btn.toggled.connect(lambda checked, s=server, l=language: self.on_server_selected(checked, s, l))
        
        return server_btn
    
    def on_server_selected(self, checked, server, language):
        """Quando um servidor é selecionado"""
        if checked:
            self.selected_server = server
            self.selected_language = language
            self.watch_btn.setEnabled(True)
            
            logger.info(f"✅ Servidor selecionado: {server.get('serverName')} ({language})")
    
    def get_selection(self):
        """Retorna a seleção do usuário"""
        return {
            'server': self.selected_server,
            'language': self.selected_language,
            'episode_data': self.episode_data
        }
    
    def mousePressEvent(self, event):
        """Permite arrastar a janela"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Permite arrastar a janela"""
        if hasattr(self, 'drag_start_position'):
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()