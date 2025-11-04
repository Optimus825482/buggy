"""
Buggy Call - VAPID Key Management
Secure handling of VAPID keys for push notifications
"""
import os
from cryptography.fernet import Fernet
import json


class VAPIDKeyManager:
    """Manager for VAPID key encryption and validation"""
    
    @staticmethod
    def get_encryption_key():
        """Get or generate encryption key"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        
        if not encryption_key:
            # Generate new key if not exists
            encryption_key = Fernet.generate_key().decode()
            print(f"Warning: Generated new encryption key. Add to .env: ENCRYPTION_KEY={encryption_key}")
        
        return encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
    
    @staticmethod
    def encrypt_private_key(private_key):
        """
        Encrypt VAPID private key
        
        Args:
            private_key: Plain text private key
            
        Returns:
            Encrypted private key as string
        """
        try:
            encryption_key = VAPIDKeyManager.get_encryption_key()
            f = Fernet(encryption_key)
            
            # Ensure private_key is bytes
            if isinstance(private_key, str):
                private_key = private_key.encode()
            
            encrypted = f.encrypt(private_key)
            return encrypted.decode()
        except Exception as e:
            print(f"Error encrypting private key: {e}")
            return None
    
    @staticmethod
    def decrypt_private_key(encrypted_key):
        """
        Decrypt VAPID private key
        
        Args:
            encrypted_key: Encrypted private key
            
        Returns:
            Decrypted private key as string
        """
        try:
            encryption_key = VAPIDKeyManager.get_encryption_key()
            f = Fernet(encryption_key)
            
            # Ensure encrypted_key is bytes
            if isinstance(encrypted_key, str):
                encrypted_key = encrypted_key.encode()
            
            decrypted = f.decrypt(encrypted_key)
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting private key: {e}")
            return None
    
    @staticmethod
    def validate_subscription(subscription_info):
        """
        Validate push subscription structure
        
        Args:
            subscription_info: Subscription info dict or JSON string
            
        Returns:
            Boolean indicating validity
            
        Raises:
            ValueError: If subscription is invalid
        """
        try:
            # Parse JSON if string
            if isinstance(subscription_info, str):
                subscription_info = json.loads(subscription_info)
            
            # Check required fields
            required_fields = ['endpoint', 'keys']
            if not all(field in subscription_info for field in required_fields):
                raise ValueError('Invalid subscription structure: missing required fields')
            
            # Check required keys
            required_keys = ['p256dh', 'auth']
            if not all(key in subscription_info['keys'] for key in required_keys):
                raise ValueError('Invalid subscription keys: missing p256dh or auth')
            
            # Validate endpoint URL
            endpoint = subscription_info['endpoint']
            if not endpoint.startswith('https://'):
                raise ValueError('Subscription endpoint must use HTTPS')
            
            return True
            
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON in subscription: {e}')
        except Exception as e:
            raise ValueError(f'Subscription validation failed: {e}')
    
    @staticmethod
    def generate_vapid_keys():
        """
        Generate new VAPID key pair
        
        Returns:
            Dict with public_key and private_key
        """
        try:
            from py_vapid import Vapid01
            
            vapid = Vapid01()
            vapid.generate_keys()
            
            return {
                'public_key': vapid.public_key.export_public().decode(),
                'private_key': vapid.private_key.export().decode()
            }
        except Exception as e:
            print(f"Error generating VAPID keys: {e}")
            return None
