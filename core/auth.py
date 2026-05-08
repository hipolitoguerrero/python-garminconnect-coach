import os
import sys
from pathlib import Path
from garminconnect import Garmin

def init_garmin_client() -> Garmin:
    """
    Initializes and returns a Garmin client.
    Attempts to restore session tokens from the local token store.
    If no valid tokens exist, prompts for credentials and MFA via environment variables.

    Returns:
        Garmin: An authenticated Garmin client instance.
    
    Raises:
        SystemExit: If authentication fails or credentials are missing.
    """
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = str(Path(tokenstore).expanduser())
    
    garmin = Garmin()
    try:
        garmin.login(tokenstore_path)
        print("Successfully authenticated using saved tokens.")
    except Exception as e:
        print(f"Token authentication failed: {e}. Falling back to credential login.")
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        if not email or not password:
            print("Error: EMAIL and PASSWORD environment variables are required.")
            sys.exit(1)
            
        garmin = Garmin(
            email=email,
            password=password,
            prompt_mfa=lambda: input("MFA code: ").strip(),
        )
        garmin.login(tokenstore_path)
    return garmin
