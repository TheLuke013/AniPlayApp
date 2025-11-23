from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                               QLineEdit, QLabel, QMessageBox, QStackedWidget, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt
from loguru import logger

from styles.dark_styles import get_dark_styles

class AuthWidget(QWidget):
    def __init__(self, auth_system, on_login_success):
        super().__init__()
        self.auth_system = auth_system
        self.on_login_success = on_login_success
        self.current_theme = "dark"
        self.init_ui()
    
    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Header com botão de tema
        header_layout = QHBoxLayout()
        
        self.setStyleSheet(get_dark_styles())
       
        #container central
        self.container = QFrame()
        self.container.setObjectName("auth_container")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        self.stacked_layout = QStackedWidget()
        container_layout.addWidget(self.stacked_layout)
        
        self.container.setLayout(container_layout)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        
        #telas
        self.login_widget = self.create_login_widget()
        self.stacked_layout.addWidget(self.login_widget)
        
        self.register_widget = self.create_register_widget()
        self.stacked_layout.addWidget(self.register_widget)
        
        self.stacked_layout.setCurrentIndex(0)
    
    def create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        #título
        title = QLabel("Bem-vindo ao AniPlay")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        #subtítulo
        subtitle = QLabel("Faça login para continuar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        #campos de input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("📧 Usuário")
        self.username_input.setMinimumHeight(45)
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("🔒 Senha")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)
        
        #botão de login
        self.login_btn = QPushButton("🎮 Entrar no AniPlay")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        #separador
        separator = QLabel("━ ou ━")
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet("color: #a0aec0; margin: 15px 0;")
        layout.addWidget(separator)
        
        #botão de registro
        self.register_btn = QPushButton("✨ Criar Nova Conta")
        self.register_btn.setObjectName("secondary")
        self.register_btn.setMinimumHeight(40)
        self.register_btn.clicked.connect(self.show_register)
        layout.addWidget(self.register_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Criar Conta")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Junte-se à comunidade AniPlay")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        #campos de registro
        self.reg_username_input = QLineEdit()
        self.reg_username_input.setPlaceholderText("👤 Escolha um usuário")
        self.reg_username_input.setMinimumHeight(45)
        layout.addWidget(self.reg_username_input)
        
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("📧 Seu melhor email")
        self.reg_email_input.setMinimumHeight(45)
        layout.addWidget(self.reg_email_input)
        
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setPlaceholderText("🔒 Crie uma senha forte")
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        self.reg_password_input.setMinimumHeight(45)
        layout.addWidget(self.reg_password_input)
        
        self.reg_confirm_password_input = QLineEdit()
        self.reg_confirm_password_input.setPlaceholderText("🔒 Confirme sua senha")
        self.reg_confirm_password_input.setEchoMode(QLineEdit.Password)
        self.reg_confirm_password_input.setMinimumHeight(45)
        layout.addWidget(self.reg_confirm_password_input)
        
        #botão de registro
        self.register_confirm_btn = QPushButton("🚀 Criar Minha Conta")
        self.register_confirm_btn.setMinimumHeight(45)
        self.register_confirm_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_confirm_btn)
        
        #botão voltar
        self.back_to_login_btn = QPushButton("↩️ Voltar para Login")
        self.back_to_login_btn.setObjectName("secondary")
        self.back_to_login_btn.setMinimumHeight(40)
        self.back_to_login_btn.clicked.connect(self.show_login)
        layout.addWidget(self.back_to_login_btn)
        
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
        
        self.login_btn.setText("🎮 Entrar no AniPlay")
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
        
        self.register_confirm_btn.setText("Criando conta...")
        self.register_confirm_btn.setEnabled(False)
        
        success, result = self.auth_system.register_user(username, email, password)
        
        self.register_confirm_btn.setText("🚀 Criar Minha Conta")
        self.register_confirm_btn.setEnabled(True)
        
        if success:
            self.show_message("Sucesso!", result, "success")
            self.show_login()
            self.clear_register_fields()
        else:
            self.show_message("Erro no Registro", result, "error")
    
    def show_register(self):
        self.stacked_layout.setCurrentIndex(1)
    
    def show_login(self):
        self.stacked_layout.setCurrentIndex(0)
    
    def clear_register_fields(self):
        self.reg_username_input.clear()
        self.reg_email_input.clear()
        self.reg_password_input.clear()
        self.reg_confirm_password_input.clear()
    
    def show_message(self, title, message, type="info"):
        colors = {
            "error": {"bg": "#2d3748", "border": "#e53e3e", "icon": "❌"},
            "warning": {"bg": "#2d3748", "border": "#dd6b20", "icon": "⚠️"}, 
            "success": {"bg": "#2d3748", "border": "#38a169", "icon": "✅"},
            "info": {"bg": "#2d3748", "border": "#3182ce", "icon": "ℹ️"}
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
                font-family: 'Segoe UI', Arial, sans-serif;
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
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
                margin: 5px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #4a5568;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #2d3748;
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

    def try_auto_login(self):
        """Tenta fazer login automático com sessão salva"""
        session = self.auth_system.load_session()
        if session:
            user_info = self.auth_system.get_user_info(session['user_id'])
            if user_info:
                self.username_input.setText(user_info['username'])
                logger.info(f"⚡ Sessão encontrada para: {user_info['username']}")
                
                msg = QMessageBox()
                msg.setWindowTitle("Sessão Salva")
                msg.setText(f"Bem-vindo de volta, {user_info['username']}!\n\nDeseja fazer login automaticamente?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)
                
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #2d3748;
                        color: #f7fafc;
                        border: 2px solid #667eea;
                        border-radius: 10px;
                    }
                    QMessageBox QLabel {
                        color: #f7fafc;
                        font-size: 14px;
                    }
                    QMessageBox QPushButton {
                        background-color: #667eea;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 8px 15px;
                        min-width: 80px;
                        margin: 5px;
                    }
                    QMessageBox QPushButton:hover {
                        background-color: #5a6fd8;
                    }
                """)
                
                if msg.exec() == QMessageBox.Yes:
                    self.password_input.setFocus()
                    self.login_btn.setStyleSheet("background-color: #38a169;")
                    self.login_btn.setText("⚡ Login Automático Disponível")
                    return True
        return False