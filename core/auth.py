import os
from pathlib import Path
from dotenv import load_dotenv
from garminconnect import Garmin

class GarminSessionManager:
    """Singleton para gestionar la persistencia de la sesión."""
    _instance = None
    
    def __init__(self, token_path: str = "~/.garminconnect"):
        load_dotenv() # Ensure env vars are loaded
        self.token_path = str(Path(token_path).expanduser())
        self.client = None

    def get_client(self) -> Garmin:
        """Devuelve un cliente autenticado, recargando la sesión si es necesario."""
        if self.client:
            return self.client
        return self._initialize_session()

    def _initialize_session(self) -> Garmin:
        """Autentica utilizando credenciales y persiste tokens."""
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        
        if not email or not password:
            raise ValueError("EMAIL and PASSWORD must be set in environment.")

        api = Garmin(email, password)
        api.login(self.token_path)
        self.client = api
        return api
