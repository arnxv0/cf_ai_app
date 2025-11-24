"""
Encrypted settings storage using SQLite.
Stores environment variables and configuration securely.
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
import base64
import logging

logger = logging.getLogger("pointer.settings")


class SettingsManager:
    """Manages encrypted storage of settings in SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None, encryption_key: Optional[bytes] = None):
        """
        Initialize the settings manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
            encryption_key: Encryption key for sensitive data. If None, generates one.
        """
        # Determine database location
        if db_path is None:
            # Use platform-appropriate data directory
            if os.name == 'posix':  # macOS/Linux
                data_dir = Path.home() / '.pointer'
            else:  # Windows
                data_dir = Path(os.getenv('APPDATA', Path.home())) / 'Pointer'
            
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / 'settings.db')
        
        self.db_path = db_path
        
        # Initialize encryption
        self._init_encryption(encryption_key)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Settings manager initialized with database at {self.db_path}")
    
    def _init_encryption(self, encryption_key: Optional[bytes] = None):
        """Initialize encryption key."""
        key_file = Path(self.db_path).parent / '.encryption_key'
        
        if encryption_key is None:
            # Try to load existing key
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    encryption_key = f.read()
            else:
                # Generate new key
                encryption_key = Fernet.generate_key()
                # Save it securely (600 permissions)
                with open(key_file, 'wb') as f:
                    f.write(encryption_key)
                os.chmod(key_file, 0o600)
        
        self.cipher = Fernet(encryption_key)
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    is_encrypted BOOLEAN DEFAULT 0,
                    is_secret BOOLEAN DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category_key 
                ON settings(category, key)
            """)
            
            conn.commit()
    
    def _encrypt(self, value: str) -> str:
        """Encrypt a value."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value."""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    def set(
        self, 
        category: str, 
        key: str, 
        value: Any, 
        is_secret: bool = False,
        description: Optional[str] = None
    ) -> bool:
        """
        Store a setting.
        
        Args:
            category: Category of the setting (e.g., 'api_keys', 'email', 'general')
            key: Setting key (e.g., 'GOOGLE_API_KEY', 'smtp_host')
            value: Setting value
            is_secret: If True, value will be encrypted
            description: Optional description of the setting
            
        Returns:
            True if successful
        """
        try:
            # Convert value to string
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # Encrypt if it's a secret
            if is_secret:
                value_str = self._encrypt(value_str)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO settings (category, key, value, is_encrypted, is_secret, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(category, key) DO UPDATE SET
                        value = excluded.value,
                        is_encrypted = excluded.is_encrypted,
                        is_secret = excluded.is_secret,
                        description = excluded.description,
                        updated_at = CURRENT_TIMESTAMP
                """, (category, key, value_str, is_secret, is_secret, description))
                conn.commit()
            
            logger.info(f"Setting saved: {category}.{key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving setting {category}.{key}: {e}")
            return False
    
    def get(
        self, 
        category: str, 
        key: str, 
        default: Any = None,
        decrypt: bool = True
    ) -> Any:
        """
        Retrieve a setting.
        
        Args:
            category: Category of the setting
            key: Setting key
            default: Default value if setting doesn't exist
            decrypt: If True, decrypt encrypted values
            
        Returns:
            Setting value or default
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, is_encrypted FROM settings WHERE category = ? AND key = ?",
                    (category, key)
                )
                row = cursor.fetchone()
                
                if row is None:
                    return default
                
                value_str, is_encrypted = row
                
                # Decrypt if necessary
                if is_encrypted and decrypt:
                    value_str = self._decrypt(value_str)
                
                # Try to parse as JSON
                try:
                    return json.loads(value_str)
                except (json.JSONDecodeError, ValueError):
                    return value_str
                    
        except Exception as e:
            logger.error(f"Error retrieving setting {category}.{key}: {e}")
            return default
    
    def get_category(
        self, 
        category: str, 
        include_secrets: bool = False,
        decrypt_secrets: bool = False
    ) -> Dict[str, Any]:
        """
        Get all settings in a category.
        
        Args:
            category: Category to retrieve
            include_secrets: If True, include secret values
            decrypt_secrets: If True, decrypt secret values
            
        Returns:
            Dictionary of key-value pairs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if include_secrets:
                    cursor = conn.execute(
                        "SELECT key, value, is_encrypted, is_secret FROM settings WHERE category = ?",
                        (category,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT key, value, is_encrypted, is_secret FROM settings WHERE category = ? AND is_secret = 0",
                        (category,)
                    )
                
                result = {}
                for key, value_str, is_encrypted, is_secret in cursor.fetchall():
                    # Decrypt if necessary
                    if is_encrypted and decrypt_secrets:
                        try:
                            value_str = self._decrypt(value_str)
                        except Exception as e:
                            logger.error(f"Error decrypting {category}.{key}: {e}")
                            continue
                    
                    # If it's a secret and we're not decrypting, mask it
                    if is_secret and not decrypt_secrets:
                        value_str = "********"
                    
                    # Try to parse as JSON
                    try:
                        result[key] = json.loads(value_str)
                    except (json.JSONDecodeError, ValueError):
                        result[key] = value_str
                
                return result
                
        except Exception as e:
            logger.error(f"Error retrieving category {category}: {e}")
            return {}
    
    def get_all_categories(self) -> List[str]:
        """Get list of all setting categories."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT category FROM settings ORDER BY category")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}")
            return []
    
    def get_all_settings(
        self, 
        include_secrets: bool = False,
        decrypt_secrets: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings grouped by category.
        
        Args:
            include_secrets: If True, include secret values
            decrypt_secrets: If True, decrypt secret values
            
        Returns:
            Dictionary of categories containing key-value pairs
        """
        categories = self.get_all_categories()
        return {
            category: self.get_category(category, include_secrets, decrypt_secrets)
            for category in categories
        }
    
    def get_setting_info(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a setting.
        
        Returns:
            Dictionary with setting information or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT is_encrypted, is_secret, description, created_at, updated_at
                    FROM settings WHERE category = ? AND key = ?
                """, (category, key))
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                return {
                    "category": category,
                    "key": key,
                    "is_encrypted": bool(row[0]),
                    "is_secret": bool(row[1]),
                    "description": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                }
        except Exception as e:
            logger.error(f"Error retrieving setting info {category}.{key}: {e}")
            return None
    
    def delete(self, category: str, key: str) -> bool:
        """Delete a setting."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM settings WHERE category = ? AND key = ?",
                    (category, key)
                )
                conn.commit()
            logger.info(f"Setting deleted: {category}.{key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting setting {category}.{key}: {e}")
            return False
    
    def delete_category(self, category: str) -> bool:
        """Delete all settings in a category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM settings WHERE category = ?", (category,))
                conn.commit()
            logger.info(f"Category deleted: {category}")
            return True
        except Exception as e:
            logger.error(f"Error deleting category {category}: {e}")
            return False
    
    def export_to_env(self, category: str = None) -> str:
        """
        Export settings as environment variable format.
        
        Args:
            category: If specified, only export this category. Otherwise export all.
            
        Returns:
            String in .env file format
        """
        if category:
            settings = {category: self.get_category(category, include_secrets=True, decrypt_secrets=True)}
        else:
            settings = self.get_all_settings(include_secrets=True, decrypt_secrets=True)
        
        lines = []
        for cat, items in settings.items():
            lines.append(f"# {cat.upper()}")
            for key, value in items.items():
                # Format value (quote if contains spaces)
                if isinstance(value, str) and ' ' in value:
                    value = f'"{value}"'
                lines.append(f"{key}={value}")
            lines.append("")  # Empty line between categories
        
        return "\n".join(lines)
    
    def import_from_env(self, env_content: str, category: str = "imported") -> int:
        """
        Import settings from .env format.
        
        Args:
            env_content: Content in .env format
            category: Category to store imported settings
            
        Returns:
            Number of settings imported
        """
        count = 0
        for line in env_content.split('\n'):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Detect if it's likely a secret
                is_secret = any(secret_keyword in key.upper() for secret_keyword in [
                    'KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'CREDENTIALS'
                ])
                
                if self.set(category, key, value, is_secret=is_secret):
                    count += 1
        
        return count


# Global instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get or create the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
