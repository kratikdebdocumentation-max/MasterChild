"""
Telegram notification utilities
"""
import requests
from config import Config

def send_telegram_message(bot_message: str, chat_id: str) -> bool:
    """
    Send a message to Telegram
    
    Args:
        bot_message: Message to send
        chat_id: Telegram chat ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        send_text = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={bot_message}'
        response = requests.get(send_text)
        return response.status_code == 200
    except Exception as e:
        print(f"Error in sending Telegram message: {e}")
        return False

def send_sos_message(bot_message: str) -> bool:
    """
    Send SOS message to Telegram
    
    Args:
        bot_message: SOS message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    return send_telegram_message(bot_message, Config.TELEGRAM_SOS_CHAT_ID)
