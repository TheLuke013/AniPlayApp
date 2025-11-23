import requests
import time
import threading
from loguru import logger

class ServerMonitor:
    def __init__(self, base_url: str = "http://localhost:4000", max_attempts: int = 30):
        self.base_url = base_url
        self.max_attempts = max_attempts
        self.is_ready = False
    
    def wait_for_server(self, callback=None):
        def check_server():
            for attempt in range(self.max_attempts):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        self.is_ready = True
                        logger.info("✅ Servidor da API está pronto!")
                        if callback:
                            callback(True)
                        return
                except requests.exceptions.RequestException:
                    pass
                
                logger.info(f"⏳ Aguardando servidor... ({attempt + 1}/{self.max_attempts})")
                time.sleep(2)
            
            logger.error("❌ Servidor não iniciou a tempo")
            if callback:
                callback(False)
        
        thread = threading.Thread(target=check_server, daemon=True)
        thread.start()