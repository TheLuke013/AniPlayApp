from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                               QLineEdit, QLabel, QMessageBox, QStackedWidget, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt
from loguru import logger

class AuthWidget(QWidget):
    def __init__(self, auth_system, on_login_success):
        super().__init__()
        self.auth_system = auth_system
        self.on_login_success = on_login_success
        self.init_ui()
    
    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com estilo escuro
        self.container = QFrame()
        self.container.setObjectName("auth_container")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # Título do AniPlay (igual ao HTML)
        title = QLabel("🎬 AniPlay")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 36px;
                margin-bottom: 20px;
                color: #ff7b00;
                font-weight: bold;
            }
        """)
        container_layout.addWidget(title)
        
        # Abas de autenticação
        auth_tabs = QWidget()
        auth_tabs_layout = QHBoxLayout()
        auth_tabs_layout.setSpacing(0)
        auth_tabs_layout.setContentsMargins(0, 0, 0, 20)
        
        self.login_tab_btn = QPushButton("Entrar")
        self.register_tab_btn = QPushButton("Cadastrar")
        
        # Estilização das abas
        tab_style = """
            QPushButton {
                padding: 12px 24px;
                border: none;
                color: white;
                background: transparent;
                border-bottom: 2px solid transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """
        
        active_tab_style = """
            QPushButton {
                border-bottom: 2px solid #ff7b00;
                color: #ff7b00;
            }
        """
        
        self.login_tab_btn.setStyleSheet(tab_style + active_tab_style)
        self.register_tab_btn.setStyleSheet(tab_style)
        
        self.login_tab_btn.clicked.connect(self.show_login)
        self.register_tab_btn.clicked.connect(self.show_register)
        
        auth_tabs_layout.addWidget(self.login_tab_btn)
        auth_tabs_layout.addWidget(self.register_tab_btn)
        auth_tabs_layout.addStretch()
        
        auth_tabs.setLayout(auth_tabs_layout)
        container_layout.addWidget(auth_tabs)
        
        # Widget stack para login/registro
        self.stacked_layout = QStackedWidget()
        container_layout.addWidget(self.stacked_layout)
        
        self.container.setLayout(container_layout)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        
        # Aplicar estilo geral
        self.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                color: white;
            }
            QFrame#auth_container {
                background: #2a2a2a;
                border-radius: 10px;
            }
        """)
        
        # Telas de login e registro
        self.login_widget = self.create_login_widget()
        self.stacked_layout.addWidget(self.login_widget)
        
        self.register_widget = self.create_register_widget()
        self.stacked_layout.addWidget(self.register_widget)
        
        self.stacked_layout.setCurrentIndex(0)
    
    def create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Campos de input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Email ou Username:")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.username_input.setMinimumHeight(45)
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha:")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)
        
        # Botão de login
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background: #ff7b00;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff9500;
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        # Link para cadastro
        switch_layout = QHBoxLayout()
        switch_label = QLabel("Não tem conta?")
        switch_label.setStyleSheet("color: #ccc;")
        
        self.switch_to_register_btn = QPushButton("Cadastre-se")
        self.switch_to_register_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff7b00;
                border: none;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                color: #ff9500;
            }
        """)
        self.switch_to_register_btn.clicked.connect(self.show_register)
        
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_to_register_btn)
        switch_layout.addStretch()
        
        layout.addLayout(switch_layout)
        widget.setLayout(layout)
        return widget
    
    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Campos de registro
        self.reg_username_input = QLineEdit()
        self.reg_username_input.setPlaceholderText("Username:")
        self.reg_username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.reg_username_input.setMinimumHeight(45)
        layout.addWidget(self.reg_username_input)
        
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("Email:")
        self.reg_email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.reg_email_input.setMinimumHeight(45)
        layout.addWidget(self.reg_email_input)
        
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setPlaceholderText("Senha:")
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        self.reg_password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.reg_password_input.setMinimumHeight(45)
        layout.addWidget(self.reg_password_input)
        
        self.reg_confirm_password_input = QLineEdit()
        self.reg_confirm_password_input.setPlaceholderText("Confirmar Senha:")
        self.reg_confirm_password_input.setEchoMode(QLineEdit.Password)
        self.reg_confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ff7b00;
            }
        """)
        self.reg_confirm_password_input.setMinimumHeight(45)
        layout.addWidget(self.reg_confirm_password_input)
        
        # Botão de registro
        self.register_confirm_btn = QPushButton("Cadastrar")
        self.register_confirm_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background: #ff7b00;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff9500;
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.register_confirm_btn.setMinimumHeight(45)
        self.register_confirm_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_confirm_btn)
        
        # Link para login
        switch_layout = QHBoxLayout()
        switch_label = QLabel("Já tem conta?")
        switch_label.setStyleSheet("color: #ccc;")
        
        self.switch_to_login_btn = QPushButton("Faça login")
        self.switch_to_login_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff7b00;
                border: none;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                color: #ff9500;
            }
        """)
        self.switch_to_login_btn.clicked.connect(self.show_login)
        
        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(self.switch_to_login_btn)
        switch_layout.addStretch()
        
        layout.addLayout(switch_layout)
        widget.setLayout(layout)
        return widget
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_message("Atenção", "Por favor, preencha todos os campos.", "warning")
            return
        
        self.login_btn.setText("Entrando...")
        self.login_btn.setEnabled(False)
        
        success, result = self.auth_system.login_user(username, password)
        
        self.login_btn.setText("Entrar")
        self.login_btn.setEnabled(True)
        
        if success:
            self.on_login_success(result)
        else:
            self.show_message("Login Falhou", result, "error")
    
    def handle_register(self):
        username = self.reg_username_input.text().strip()
        email = self.reg_email_input.text().strip()
        password = self.reg_password_input.text()
        confirm_password = self.reg_confirm_password_input.text()
        
        if not all([username, email, password, confirm_password]):
            self.show_message("Atenção", "Por favor, preencha todos os campos.", "warning")
            return
        
        if password != confirm_password:
            self.show_message("Erro", "As senhas não coincidem.", "error")
            return
        
        if len(password) < 6:
            self.show_message("Erro", "A senha deve ter pelo menos 6 caracteres.", "error")
            return
        
        if len(username) < 3:
            self.show_message("Erro", "O usuário deve ter pelo menos 3 caracteres.", "error")
            return
        
        self.register_confirm_btn.setText("Cadastrando...")
        self.register_confirm_btn.setEnabled(False)
        
        success, result = self.auth_system.register_user(username, email, password)
        
        self.register_confirm_btn.setText("Cadastrar")
        self.register_confirm_btn.setEnabled(True)
        
        if success:
            self.show_message("Sucesso!", result, "success")
            self.show_login()
            self.clear_register_fields()
        else:
            self.show_message("Erro no Registro", result, "error")
    
    def show_register(self):
        self.stacked_layout.setCurrentIndex(1)
        self.login_tab_btn.setStyleSheet(self.get_tab_style(False))
        self.register_tab_btn.setStyleSheet(self.get_tab_style(True))
    
    def show_login(self):
        self.stacked_layout.setCurrentIndex(0)
        self.login_tab_btn.setStyleSheet(self.get_tab_style(True))
        self.register_tab_btn.setStyleSheet(self.get_tab_style(False))
    
    def get_tab_style(self, active):
        base_style = """
            QPushButton {
                padding: 12px 24px;
                border: none;
                color: white;
                background: transparent;
                border-bottom: 2px solid transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
        """
        active_style = """
            QPushButton {
                border-bottom: 2px solid #ff7b00;
                color: #ff7b00;
            }
        """
        return base_style + (active_style if active else "")
    
    def clear_register_fields(self):
        self.reg_username_input.clear()
        self.reg_email_input.clear()
        self.reg_password_input.clear()
        self.reg_confirm_password_input.clear()
    
    def show_message(self, title, message, type="info"):
        colors = {
            "error": {"bg": "#2a2a2a", "border": "#e53e3e", "icon": "❌"},
            "warning": {"bg": "#2a2a2a", "border": "#dd6b20", "icon": "⚠️"}, 
            "success": {"bg": "#2a2a2a", "border": "#38a169", "icon": "✅"},
            "info": {"bg": "#2a2a2a", "border": "#3182ce", "icon": "ℹ️"}
        }
        
        color_info = colors.get(type, colors["info"])
        
        msg = QMessageBox()
        msg.setWindowTitle(f"{color_info['icon']} {title}")
        msg.setText(message)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {color_info['bg']};
                color: #f7fafc;
                border: 2px solid {color_info['border']};
                border-radius: 10px;
            }}
            QMessageBox QLabel {{
                color: #f7fafc;
                font-size: 14px;
                padding: 10px;
            }}
            QMessageBox QPushButton {{
                background-color: {color_info['border']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 12px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #4a5568;
            }}
        """)
        
        if type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif type == "success":
            msg.setIcon(QMessageBox.Information)
        else:
            msg.setIcon(QMessageBox.Information)
        
        msg.exec()

    def show_register_tab(self):
        """Método para ser chamado externamente para mostrar a aba de registro"""
        self.show_register()

    def show_login_tab(self):
        """Método para ser chamado externamente para mostrar a aba de login"""
        self.show_login()