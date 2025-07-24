#!/usr/bin/env python3
"""
Bybit API to Telegram Bot Script - Enhanced Version

This script fetches cryptocurrency prices from Bybit API and sends updates to a Telegram chat.
It has been improved with better error handling, logging, modularity, and compatibility with
older versions of the Bybit API.

SETUP INSTRUCTIONS:
1. Install dependencies: pip install -r requirements.txt
2. Create a .env file based on .env.example with your API credentials:
   - BYBIT_API_KEY: Your Bybit API key
   - BYBIT_API_SECRET: Your Bybit API secret  
   - TELEGRAM_BOT_TOKEN: Your Telegram bot token (get from @BotFather)
   - TELEGRAM_CHAT_ID: Your Telegram chat ID (use @userinfobot to get it)
3. Run the script: python bybit_telegram_bot.py

FEATURES:
- Compatible with older Bybit API versions using get_ticker method
- Comprehensive error handling and logging
- Modular code structure for maintainability
- Configurable via environment variables
- Network retry logic for reliability
"""

import os
import time
import logging
import requests
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import sys

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BybitTelegramBot:
    """
    A bot that fetches cryptocurrency prices from Bybit API and sends updates to Telegram.
    
    This class handles API connections, error management, and message delivery with
    proper logging and retry mechanisms.
    """
    
    def __init__(self):
        """Initialize the bot with configuration from environment variables."""
        self.api_key = os.getenv('BYBIT_API_KEY', '')
        self.api_secret = os.getenv('BYBIT_API_SECRET', '')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.symbol = os.getenv('SYMBOL', 'BTCUSDT')
        self.update_interval = int(os.getenv('UPDATE_INTERVAL', '60'))
        
        # Validate required environment variables
        self._validate_config()
        
        # Initialize Bybit session with error handling
        try:
            self.session = HTTP(
                testnet=False,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            logger.info("Bybit API session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bybit API session: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validate that all required configuration is present."""
        required_vars = {
            'BYBIT_API_KEY': self.api_key,
            'BYBIT_API_SECRET': self.api_secret,
            'TELEGRAM_BOT_TOKEN': self.telegram_token,
            'TELEGRAM_CHAT_ID': self.chat_id
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current price for a symbol using the get_tickers method (compatible with older API versions).
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Optional[float]: Current price or None if retrieval failed
            
        Note:
            Uses get_tickers instead of get_market_ticker for compatibility with older Bybit API versions.
        """
        try:
            logger.debug(f"Fetching price for symbol: {symbol}")
            
            # Use get_tickers method for compatibility with older Bybit API versions
            response = self.session.get_tickers(
                category="spot",
                symbol=symbol
            )
            
            # Validate API response structure
            if not response or 'result' not in response:
                logger.error(f"Invalid API response structure: {response}")
                return None
            
            result = response['result']
            
            # Check if we have list data
            if 'list' not in result or not result['list']:
                logger.error(f"No ticker data found for symbol {symbol}")
                return None
            
            # Get the first (and should be only) ticker data
            ticker_data = result['list'][0]
            
            # Extract price from response
            last_price = ticker_data.get('lastPrice')
            
            if last_price is None:
                logger.error(f"Price data not found in response: {ticker_data}")
                return None
            
            price = float(last_price)
            logger.info(f"Successfully fetched price for {symbol}: ${price}")
            return price
            
        except ValueError as e:
            logger.error(f"Error converting price to float for {symbol}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Missing key in API response for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {symbol}: {e}")
            return None
    
    def send_telegram_message(self, message: str, max_retries: int = 3) -> bool:
        """
        Send a message to Telegram chat with retry logic and comprehensive error handling.
        
        Args:
            message (str): Message to send
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'  # Enable HTML formatting
        }
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending Telegram message (attempt {attempt + 1}/{max_retries})")
                
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()  # Raise exception for bad status codes
                
                response_data = response.json()
                if response_data.get('ok'):
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {response_data.get('description', 'Unknown error')}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout sending Telegram message (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error sending Telegram message (attempt {attempt + 1})")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error sending Telegram message: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error sending Telegram message: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending Telegram message: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        logger.error("Failed to send Telegram message after all retry attempts")
        return False
    
    def format_price_message(self, symbol: str, price: float) -> str:
        """
        Format price information into a readable message.
        
        Args:
            symbol (str): Trading pair symbol
            price (float): Current price
            
        Returns:
            str: Formatted message
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        return f"🔄 <b>Price Update</b>\n📊 Symbol: {symbol}\n💰 Price: ${price:,.4f}\n⏰ Time: {timestamp}"
    
    def run(self) -> None:
        """
        Main bot loop that fetches prices and sends updates to Telegram.
        
        Runs continuously until interrupted, with proper error handling and logging.
        """
        logger.info(f"Starting Bybit Telegram Bot for symbol: {self.symbol}")
        logger.info(f"Update interval: {self.update_interval} seconds")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    # Fetch current price
                    price = self.get_current_price(self.symbol)
                    
                    if price is not None:
                        # Format and send message
                        message = self.format_price_message(self.symbol, price)
                        success = self.send_telegram_message(message)
                        
                        if success:
                            consecutive_errors = 0  # Reset error counter on success
                        else:
                            consecutive_errors += 1
                            logger.warning(f"Consecutive errors: {consecutive_errors}")
                    else:
                        consecutive_errors += 1
                        logger.warning(f"Failed to fetch price. Consecutive errors: {consecutive_errors}")
                    
                    # Check if we have too many consecutive errors
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive errors ({consecutive_errors}). Stopping bot.")
                        break
                    
                    # Wait before next update
                    logger.debug(f"Waiting {self.update_interval} seconds until next update...")
                    time.sleep(self.update_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Bot stopped by user")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Unexpected error in main loop: {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive errors. Stopping bot.")
                        break
                    
                    # Wait before retrying
                    time.sleep(min(60, self.update_interval))
                    
        except Exception as e:
            logger.error(f"Fatal error in bot: {e}")
            raise
        finally:
            logger.info("Bot stopped")


def main():
    """
    Main entry point for the script.
    
    Creates and runs the Bybit Telegram Bot with proper error handling.
    """
    try:
        bot = BybitTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()