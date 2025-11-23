def get_auth_styles():
    return """
    /* Estilos Gerais */
    QWidget {
        font-family: 'Segoe UI', Arial, sans-serif;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                   stop:0 #667eea, stop:1 #764ba2);
    }
    
    /* Container Principal */
    QWidget#auth_container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 30px;
    }
    
    /* Títulos */
    QLabel {
        color: #2d3748;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        background: transparent;
        border: none;
    }
    
    QLabel#subtitle {
        color: #718096;
        font-size: 14px;
        font-weight: normal;
        margin-bottom: 30px;
    }
    
    /* Campos de Input */
    QLineEdit {
        background: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 14px;
        color: #2d3748;
        margin-bottom: 15px;
        min-height: 20px;
    }
    
    QLineEdit:focus {
        border-color: #667eea;
        background: #ffffff;
    }
    
    QLineEdit::placeholder {
        color: #a0aec0;
    }
    
    /* Botões Principais */
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
        margin-top: 10px;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #5a6fd8, stop:1 #6a4190);
    }
    
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #4c5bc6, stop:1 #58357e);
    }
    
    /* Botões Secundários */
    QPushButton#secondary {
        background: transparent;
        color: #667eea;
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        margin-top: 5px;
    }
    
    QPushButton#secondary:hover {
        background: #667eea;
        color: white;
    }
    
    /* Cards/Containers Internos */
    QFrame {
        background: white;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    
    /* Mensagens de Erro/Sucesso */
    QLabel#error {
        color: #e53e3e;
        font-size: 12px;
        background: #fed7d7;
        padding: 8px;
        border-radius: 5px;
        border: 1px solid #feb2b2;
    }
    
    QLabel#success {
        color: #38a169;
        font-size: 12px;
        background: #c6f6d5;
        padding: 8px;
        border-radius: 5px;
        border: 1px solid #9ae6b4;
    }
    
    /* Loading Spinner */
    QProgressBar {
        border: none;
        background: #e2e8f0;
        border-radius: 10px;
        text-align: center;
        color: #4a5568;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #667eea, stop:1 #764ba2);
        border-radius: 10px;
    }
    """