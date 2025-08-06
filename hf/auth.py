"""Hugging Face authentication management."""

import os
from pathlib import Path
from huggingface_hub import login, whoami, HfApi
from huggingface_hub.utils import RepositoryNotFoundError
from database.models_db import get_app_data_dir
from typing import Optional, Dict

def get_hf_token_path() -> Path:
    """Get path where HF token is stored."""
    return get_app_data_dir() / 'hf_token.txt'

def save_hf_token(token: str) -> bool:
    """Save HF token to local file."""
    try:
        token_path = get_hf_token_path()
        with open(token_path, 'w') as f:
            f.write(token.strip())
        return True
    except Exception as e:
        print(f"Error saving HF token: {e}")
        return False

def load_hf_token() -> Optional[str]:
    """Load HF token from local file."""
    try:
        token_path = get_hf_token_path()
        if token_path.exists():
            with open(token_path, 'r') as f:
                return f.read().strip()
        return None
    except Exception as e:
        print(f"Error loading HF token: {e}")
        return None

def is_authenticated() -> bool:
    """Check if user is authenticated with Hugging Face."""
    try:
        # First check if there's a token in our local storage
        token = load_hf_token()
        if token:
            # Try to use the token
            api = HfApi(token=token)
            user_info = api.whoami()
            return user_info is not None
        
        # Check if already logged in via HF CLI or environment
        try:
            user_info = whoami()
            return user_info is not None
        except:
            pass
            
        return False
    except Exception:
        return False

def get_user_info() -> Optional[Dict]:
    """Get current user information if authenticated."""
    try:
        # Try our local token first
        token = load_hf_token()
        if token:
            api = HfApi(token=token)
            return api.whoami()
        
        # Try system authentication
        return whoami()
    except Exception:
        return None

def authenticate(token: str) -> Dict[str, any]:
    """Authenticate with Hugging Face using a token.
    
    Returns:
        Dict with 'success', 'message', and optionally 'user_info'
    """
    try:
        # Validate token format (starts with hf_)
        if not token.startswith('hf_'):
            return {
                'success': False,
                'message': 'Invalid token format. HF tokens should start with "hf_"'
            }
        
        # Test the token
        api = HfApi(token=token)
        user_info = api.whoami()
        
        if user_info:
            # Save token locally
            if save_hf_token(token):
                # Set environment variable for this session
                os.environ['HUGGINGFACE_HUB_TOKEN'] = token
                
                return {
                    'success': True,
                    'message': f'Successfully authenticated as {user_info.get("name", "unknown")}',
                    'user_info': user_info
                }
            else:
                return {
                    'success': False,
                    'message': 'Authentication successful but failed to save token locally'
                }
        else:
            return {
                'success': False,
                'message': 'Invalid token - authentication failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Authentication error: {str(e)}'
        }

def logout() -> bool:
    """Log out by removing stored token."""
    try:
        token_path = get_hf_token_path()
        if token_path.exists():
            token_path.unlink()
        
        # Remove from environment
        if 'HUGGINGFACE_HUB_TOKEN' in os.environ:
            del os.environ['HUGGINGFACE_HUB_TOKEN']
            
        return True
    except Exception as e:
        print(f"Error during logout: {e}")
        return False

def auto_authenticate():
    """Automatically authenticate if token is available."""
    try:
        token = load_hf_token()
        if token:
            os.environ['HUGGINGFACE_HUB_TOKEN'] = token
            return True
        return False
    except Exception:
        return False

# Auto-authenticate on import
auto_authenticate()