def get_dark_styles():
    return """
    /* Tema Escuro - CORRIGIDO */
    QWidget {
        font-family: 'Segoe UI', Arial, sans-serif;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                   stop:0 #1a202c, stop:1 #2d3748);
        color: #f7fafc; /* 🔥 CORRIGIDO: Cor do texto padrão */
    }
    
    QWidget#auth_container {
        background: rgba(45, 55, 72, 0.95);
        border-radius: 15px;
        border: 1px solid #4a5568;
        padding: 30px;
    }
    
    /* 🔥 CORRIGIDO: Estilo explícito para QLabel */
    QLabel {
        color: #f7fafc !important;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        background: transparent;
        border: none;
        padding: 5px;
    }
    
    QLabel#subtitle {
        color: #a0aec0 !important;
        font-size: 14px;
        font-weight: normal;
        margin-bottom: 20px;
    }
    
    QLineEdit {
        background: #2d3748;
        border: 2px solid #4a5568;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 14px;
        color: #f7fafc;
        margin-bottom: 15px;
        min-height: 20px;
    }
    
    QLineEdit:focus {
        border-color: #667eea;
        background: #1a202c;
    }
    
    QLineEdit::placeholder {
        color: #718096;
    }
    
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
    
    /* 🔥 ADICIONADO: Estilo para o separador */
    QLabel[objectName="separator"] {
        color: #a0aec0;
        background: transparent;
        padding: 10px;
        margin: 10px 0;
    }
    """