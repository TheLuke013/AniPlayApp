from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal

class HeaderWidget(QWidget):
    login_clicked = Signal()
    register_clicked = Signal()
    logout_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
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

        self.welcome_label = QLabel("Olá, <span style='color: #ff7b00; font-weight: bold;'>Usuário</span>!")
        self.welcome_label.setStyleSheet("color: #ccc;")
        self.welcome_label.hide()

        self.login_btn = QPushButton("Entrar")
        self.register_btn = QPushButton("Cadastrar")
        self.logout_btn = QPushButton("Sair")
        self.logout_btn.hide()

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

        self.setLayout(layout)
        
        # Conectar sinais
        self.login_btn.clicked.connect(self.login_clicked.emit)
        self.register_btn.clicked.connect(self.register_clicked.emit)
        self.logout_btn.clicked.connect(self.logout_clicked.emit)
    
    def update_user_info(self, username):
        """Atualiza as informações do usuário no header"""
        if username:
            self.welcome_label.setText(f"Olá, <span style='color: #ff7b00; font-weight: bold;'>{username}</span>!")
            self.welcome_label.show()
            self.login_btn.hide()
            self.register_btn.hide()
            self.logout_btn.show()
        else:
            self.welcome_label.hide()
            self.login_btn.show()
            self.register_btn.show()
            self.logout_btn.hide()