import sqlite3
import re
from pathlib import Path
from passlib.context import CryptContext
import jwt
import datetime
from loguru import logger
import json

class AuthSystem:
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["sha256_crypt"],
            deprecated="auto",
            sha256_crypt__default_rounds=30000
        )
        self.secret_key = "0132456789ABCDEF"
        self.setup_database()
        logger.info("✅ Sistema de auth inicializado com SHA256")

        try:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            test_hash = self.pwd_context.hash("test")
            logger.info("Backend bcrypt carregado com sucesso")
        except Exception as e:
            logger.warning(f"bcrypt não disponível: {e}, usando sha256_crypt")
            self.pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    
    def setup_database(self):
        db_path = self.get_app_data_path() / "users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Banco de dados de usuários inicializado")
    
    def get_app_data_path(self):
        app_data = Path.home() / "AppData" / "Local" / "AniPlay"
        app_data.mkdir(exist_ok=True)
        return app_data
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username):
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return re.match(pattern, username) is not None
    
    def hash_password(self, password):
        try:
            if len(password) > 72:
                logger.warning("Senha muito longa, truncando para 72 caracteres")
                password = password[:72]
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Erro ao fazer hash da senha: {e}")
            raise
    
    def verify_password(self, password, hashed):
        try:
            if len(password) > 72:
                password = password[:72]
            return self.pwd_context.verify(password, hashed)
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    def register_user(self, username, email, password):
        try:
            if not self.validate_username(username):
                return False, "Usuário deve conter apenas letras, números e underscores (3-20 caracteres)"
            
            if not self.validate_email(email):
                return False, "Email inválido"
            
            if len(password) < 6:
                return False, "Senha deve ter pelo menos 6 caracteres"
            
            db_path = self.get_app_data_path() / "users.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                         (username, email))
            if cursor.fetchone():
                return False, "Usuário ou email já existe"
            
            password_hash = self.hash_password(password)
            
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            self.create_user_database(user_id)
            
            logger.info(f"Novo usuário registrado: {username} (ID: {user_id})")
            return True, "Usuário registrado com sucesso!"
            
        except sqlite3.IntegrityError:
            return False, "Usuário ou email já existe"
        except Exception as e:
            logger.error(f"Erro no registro: {e}")
            return False, f"Erro interno no sistema: {str(e)}"
    
    def login_user(self, username, password):
        try:
            db_path = self.get_app_data_path() / "users.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?", 
                (username,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, "Usuário não encontrado"
            
            user_id, db_username, password_hash = result
            
            if self.verify_password(password, password_hash):
                token = jwt.encode({
                    'user_id': user_id,
                    'username': db_username,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
                }, self.secret_key, algorithm='HS256')
                
                logger.info(f"Login bem-sucedido: {username}")
                return True, token
            else:
                return False, "Senha incorreta"
                
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False, f"Erro interno no sistema: {str(e)}"

    def create_user_database(self, user_id):
        """Cria banco de dados pessoal para o usuário"""
        try:
            user_db_path = self.get_app_data_path() / f"user_{user_id}.db"
            conn = sqlite3.connect(user_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'dark',
                    language TEXT DEFAULT 'pt-BR',
                    auto_play INTEGER DEFAULT 1,
                    default_quality TEXT DEFAULT '1080p',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,  -- 🔥 COLUNA ADICIONADA
                    anime_id TEXT NOT NULL,
                    anime_title TEXT NOT NULL,
                    anime_image TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES preferences (user_id),
                    UNIQUE(user_id, anime_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watch_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,  -- 🔥 COLUNA ADICIONADA
                    anime_id TEXT NOT NULL,
                    anime_title TEXT NOT NULL,
                    episode_number INTEGER,
                    episode_title TEXT,
                    progress_seconds INTEGER DEFAULT 0,
                    total_seconds INTEGER DEFAULT 0,
                    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES preferences (user_id)
                )
            ''')
            
            cursor.execute(
                "INSERT OR IGNORE INTO preferences (user_id) VALUES (?)",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Banco de dados do usuário {user_id} criado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar banco do usuário {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, "Token expirado"
        except jwt.InvalidTokenError:
            return False, "Token inválido"

    def save_session(self, user_id, token):
        try:
            session_path = self.get_app_data_path() / "session.json"
            session_data = {
                'user_id': user_id,
                'token': token,
                'saved_at': datetime.datetime.now().isoformat()
            }
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Sessão salva para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão: {e}")
            return False

    def load_session(self):
        try:
            session_path = self.get_app_data_path() / "session.json"
            
            if not session_path.exists():
                logger.info("ℹ️ Nenhuma sessão encontrada")
                return None
            
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            token = session_data.get('token')
            user_id = session_data.get('user_id')
            
            if not token or not user_id:
                logger.warning("⚠️ Sessão corrompida ou incompleta")
                self.clear_session()
                return None
            
            # Verifica se o token ainda é válido
            success, payload = self.verify_token(token)
            if success:
                logger.info(f"✅ Sessão carregada para usuário {payload.get('username', 'Unknown')}")
                return payload
            
            logger.warning("⚠️ Token expirado ou inválido")
            self.clear_session()
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar sessão (arquivo corrompido): {e}")
            self.clear_session()
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao carregar sessão: {e}")
            return None

    def clear_session(self):
        try:
            session_path = self.get_app_data_path() / "session.json"
            if session_path.exists():
                session_path.unlink()
                logger.info("✅ Sessão removida")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao limpar sessão: {e}")
            return False

    def get_user_info(self, user_id):
        try:
            db_path = self.get_app_data_path() / "users.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT username, email FROM users WHERE id = ?", 
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                username, email = result
                return {'user_id': user_id, 'username': username, 'email': email}
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter info do usuário: {e}")
            return None