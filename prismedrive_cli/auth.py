import os
import click # For click.echo in user messages

# Define a simple location for the token file within the project for now.
# This is still not ideal for production but better than a global variable for persistence.
# A common place would be ~/.config/prismdrive_cli/token.txt
# For simplicity during development, let's place it in the project root,
# but ensure it's in .gitignore.
TOKEN_FILE_NAME = ".prismdrive_token"
# Determine project root (assuming auth.py is one level down in prismedrive_cli)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE_PATH = os.path.join(PROJECT_ROOT, TOKEN_FILE_NAME)

_current_token = None # In-memory cache of the token

def _save_token_to_file(token):
    """Saves the token to a local file."""
    try:
        with open(TOKEN_FILE_PATH, "w") as f:
            f.write(token)
        # click.echo(f"Token saved to {TOKEN_FILE_PATH}", err=True) # Debug
    except IOError as e:
        click.echo(f"Error saving token: {e}", err=True)

def _load_token_from_file():
    """Loads the token from a local file."""
    try:
        with open(TOKEN_FILE_PATH, "r") as f:
            token = f.read().strip()
            return token if token else None
    except FileNotFoundError:
        return None
    except IOError as e:
        click.echo(f"Error loading token: {e}", err=True)
        return None

def _clear_token_file():
    """Clears the stored token file."""
    try:
        if os.path.exists(TOKEN_FILE_PATH):
            os.remove(TOKEN_FILE_PATH)
        # click.echo("Token file cleared.", err=True) # Debug
    except IOError as e:
        click.echo(f"Error clearing token file: {e}", err=True)


def login(api_client, email, password, device_name="prismdrive-cli"):
    """
    Logs in the user, stores the token, and updates the api_client.
    """
    global _current_token
    click.echo(f"Attempting login for {email}...")
    response = api_client.login(email, password, device_name)

    if response and not response.get("error"):
        # The Swagger indicates the token is directly in response.user.access_token
        user_data = response.get("user")
        if user_data and "access_token" in user_data:
            _current_token = user_data["access_token"]
            api_client.set_token(_current_token)
            _save_token_to_file(_current_token)
            click.echo("Login successful. Token acquired and saved.")
            return True
        else:
            click.echo("Login response did not contain an access token.", err=True)
            _current_token = None
            api_client.clear_token()
            _clear_token_file()
            return False
    else:
        error_message = response.get("message", "Unknown login error.") if response else "Login request failed."
        click.echo(f"Login failed: {error_message}", err=True)
        _current_token = None
        api_client.clear_token()
        _clear_token_file()
        return False

def logout(api_client):
    """
    Logs out the user by clearing the token from memory, file, and api_client.
    """
    global _current_token
    _current_token = None
    if api_client:
        api_client.clear_token()
    _clear_token_file()
    click.echo("Logout successful. Token cleared.")
    return True

def get_token(api_client=None):
    """
    Retrieves the current access token, loading from file if not in memory.
    Also ensures the api_client (if provided) has the token set.
    """
    global _current_token
    
    # 1. Check in-memory cache
    if _current_token:
        if api_client and not api_client.token:
            api_client.set_token(_current_token)
        return _current_token

    # 2. Check environment variable
    env_token = os.environ.get('PRISMDRIVE_TOKEN')
    if env_token:
        # click.echo("Using token from PRISMDRIVE_TOKEN environment variable.", err=True) # Debug
        _current_token = env_token
        if api_client:
            api_client.set_token(_current_token)
        # Optionally, we could save this to the file as well, or just use it for the session
        # For now, let's not auto-save env token to file to keep env var as override
        return _current_token

    # 3. Load from file
    file_token = _load_token_from_file()
    if file_token:
        _current_token = file_token
        if api_client:
            api_client.set_token(_current_token)
        return _current_token
    
    # If no token found anywhere, and api_client had one, clear it from api_client
    if api_client and api_client.token:
        api_client.clear_token()
        
    return None # No token found

def ensure_authenticated(func):
    """
    A decorator to ensure that a command is run by an authenticated user.
    """
    def wrapper(*args, **kwargs):
        if not get_token():
            print("Authentication required. Please login first using 'prismdrive login'.")
            return
        return func(*args, **kwargs)
    return wrapper

# --- Placeholder token storage functions (to be replaced) ---
# def save_token(token):
#     os.makedirs(CONFIG_DIR, exist_ok=True)
#     with open(TOKEN_FILE, "w") as f:
#         f.write(token)
#     print("Token saved (placeholder).")

# def load_token():
#     try:
#         with open(TOKEN_FILE, "r") as f:
#             return f.read().strip()
#     except FileNotFoundError:
#         return None

# def clear_stored_token():
#     try:
#         os.remove(TOKEN_FILE)
#         print("Stored token cleared (placeholder).")
#     except FileNotFoundError:
#         pass # No token to clear

if __name__ == '__main__':
    # Example usage
    # Simulating a login
    # login(None, "test@example.com", "password") # api_client would be needed
    # print(f"Current token: {get_token()}")
    # logout()
    # print(f"Current token after logout: {get_token()}")
    pass