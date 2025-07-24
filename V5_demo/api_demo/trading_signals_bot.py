"""
Bybit API v5 Trading Signals Bot with Telegram Integration

This script demonstrates how to:
1. Use Bybit API v5 for getting market data (get_market_ticker instead of deprecated get_ticker)
2. Integrate with Telegram for trading signals
3. Handle errors properly
4. Use modern API v5 endpoints

Requirements:
- pip install requests
- pip install python-telegram-bot
- Bybit API credentials
- Telegram Bot Token
"""

import requests
import time
import hashlib
import hmac
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BybitAPIv5:
    """
    Bybit API v5 client for trading signals
    """
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.recv_window = 5000
        
        # Use testnet by default for safety
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
            
        self.session = requests.Session()
        logger.info(f"Initialized Bybit API v5 client - Testnet: {testnet}")
    
    def _generate_signature(self, timestamp: str, payload: str) -> str:
        """Generate HMAC signature for API requests"""
        param_str = f"{timestamp}{self.api_key}{self.recv_window}{payload}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request to Bybit API v5
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Response data or None if error
        """
        try:
            timestamp = str(int(time.time() * 1000))
            
            if method == "GET":
                query_string = ""
                if params:
                    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                payload = query_string
                url = f"{self.base_url}{endpoint}"
                if query_string:
                    url += f"?{query_string}"
            else:
                payload = json.dumps(params) if params else ""
                url = f"{self.base_url}{endpoint}"
            
            signature = self._generate_signature(timestamp, payload)
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-SIGN': signature,
                'X-BAPI-SIGN-TYPE': '2',
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-RECV-WINDOW': str(self.recv_window),
                'Content-Type': 'application/json'
            }
            
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, headers=headers, data=payload, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            return None
    
    def get_market_ticker(self, category: str = "spot", symbol: str = "BTCUSDT") -> Optional[Dict]:
        """
        Get market ticker information using API v5 (replaces deprecated get_ticker)
        
        Args:
            category: Product category (spot, linear, inverse, option)
            symbol: Trading symbol
            
        Returns:
            Ticker data or None if error
        """
        endpoint = "/v5/market/tickers"
        params = {
            "category": category,
            "symbol": symbol
        }
        
        try:
            response = self._make_request("GET", endpoint, params)
            if response and response.get("retCode") == 0:
                result = response.get("result", {})
                ticker_list = result.get("list", [])
                if ticker_list:
                    return ticker_list[0]  # Return first ticker
                else:
                    logger.warning(f"No ticker data found for {symbol}")
                    return None
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"API error getting ticker for {symbol}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting market ticker for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str = "BTCUSDT", category: str = "spot") -> Optional[float]:
        """
        Get current price for a symbol using API v5
        
        Args:
            symbol: Trading symbol
            category: Product category
            
        Returns:
            Current price as float or None if error
        """
        ticker_data = self.get_market_ticker(category=category, symbol=symbol)
        
        if ticker_data:
            # API v5 returns price in 'lastPrice' field
            price_str = ticker_data.get("lastPrice")
            if price_str:
                try:
                    return float(price_str)
                except ValueError:
                    logger.error(f"Invalid price format: {price_str}")
                    return None
            else:
                logger.error(f"No lastPrice found in ticker data for {symbol}")
                return None
        
        return None
    
    def get_kline_data(self, symbol: str = "BTCUSDT", interval: str = "1", 
                       category: str = "spot", limit: int = 200) -> Optional[list]:
        """
        Get kline/candlestick data
        
        Args:
            symbol: Trading symbol
            interval: Time interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            category: Product category
            limit: Number of records to return
            
        Returns:
            List of kline data or None if error
        """
        endpoint = "/v5/market/kline"
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        response = self._make_request("GET", endpoint, params)
        if response and response.get("retCode") == 0:
            result = response.get("result", {})
            return result.get("list", [])
        
        return None


class TelegramBot:
    """
    Simple Telegram bot for sending trading signals
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        logger.info("Initialized Telegram bot")
    
    def send_message(self, message: str) -> bool:
        """
        Send message to Telegram chat
        
        Args:
            message: Message text to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False


class TradingSignalsBot:
    """
    Main trading signals bot that combines Bybit API v5 and Telegram
    """
    
    def __init__(self, bybit_api: BybitAPIv5, telegram_bot: TelegramBot):
        self.bybit_api = bybit_api
        self.telegram_bot = telegram_bot
        self.last_prices = {}  # Store last known prices
        logger.info("Trading signals bot initialized")
    
    def analyze_price_movement(self, symbol: str, current_price: float, 
                             threshold_percent: float = 2.0) -> Optional[str]:
        """
        Analyze price movement and generate signal if significant change
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            threshold_percent: Percentage change threshold for signal
            
        Returns:
            Signal message or None
        """
        if symbol not in self.last_prices:
            self.last_prices[symbol] = current_price
            return None
        
        last_price = self.last_prices[symbol]
        price_change = ((current_price - last_price) / last_price) * 100
        
        if abs(price_change) >= threshold_percent:
            direction = "📈 UP" if price_change > 0 else "📉 DOWN"
            signal = (
                f"🚨 <b>PRICE ALERT</b> 🚨\n"
                f"Symbol: <b>{symbol}</b>\n"
                f"Direction: {direction}\n"
                f"Current Price: <b>${current_price:.2f}</b>\n"
                f"Previous Price: <b>${last_price:.2f}</b>\n"
                f"Change: <b>{price_change:+.2f}%</b>\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Update last price
            self.last_prices[symbol] = current_price
            return signal
        
        return None
    
    def get_market_summary(self, symbols: list = None) -> str:
        """
        Get market summary for multiple symbols
        
        Args:
            symbols: List of symbols to check
            
        Returns:
            Formatted market summary
        """
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"]
        
        summary = "📊 <b>MARKET SUMMARY</b> 📊\n\n"
        
        for symbol in symbols:
            try:
                price = self.bybit_api.get_current_price(symbol)
                if price:
                    ticker_data = self.bybit_api.get_market_ticker(symbol=symbol)
                    if ticker_data:
                        change_24h = ticker_data.get("price24hPcnt", "N/A")
                        volume_24h = ticker_data.get("volume24h", "N/A")
                        
                        summary += (
                            f"<b>{symbol}</b>\n"
                            f"Price: ${price:.4f}\n"
                            f"24h Change: {change_24h}%\n"
                            f"24h Volume: {volume_24h}\n\n"
                        )
                    else:
                        summary += f"<b>{symbol}</b>: Error getting data\n\n"
                else:
                    summary += f"<b>{symbol}</b>: Price unavailable\n\n"
                    
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {e}")
                summary += f"<b>{symbol}</b>: Error - {str(e)}\n\n"
        
        summary += f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return summary
    
    def run_monitoring(self, symbols: list = None, check_interval: int = 60, 
                      price_threshold: float = 2.0):
        """
        Run continuous price monitoring
        
        Args:
            symbols: List of symbols to monitor
            check_interval: Check interval in seconds
            price_threshold: Price change threshold for alerts
        """
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT"]
        
        logger.info(f"Starting price monitoring for {symbols}")
        
        # Send initial market summary
        summary = self.get_market_summary(symbols)
        self.telegram_bot.send_message(summary)
        
        try:
            while True:
                for symbol in symbols:
                    try:
                        current_price = self.bybit_api.get_current_price(symbol)
                        if current_price:
                            logger.info(f"{symbol}: ${current_price:.4f}")
                            
                            # Check for significant price movement
                            signal = self.analyze_price_movement(
                                symbol, current_price, price_threshold
                            )
                            
                            if signal:
                                self.telegram_bot.send_message(signal)
                        else:
                            logger.warning(f"Could not get price for {symbol}")
                            
                    except Exception as e:
                        logger.error(f"Error monitoring {symbol}: {e}")
                
                logger.info(f"Waiting {check_interval} seconds...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            error_msg = f"❌ Bot Error: {str(e)}"
            self.telegram_bot.send_message(error_msg)


def main():
    """
    Main function - Example usage
    """
    # Configuration (replace with your actual credentials)
    BYBIT_API_KEY = "YOUR_BYBIT_API_KEY"
    BYBIT_SECRET_KEY = "YOUR_BYBIT_SECRET_KEY"
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
    
    # Use testnet for safety
    USE_TESTNET = True
    
    try:
        # Initialize APIs
        bybit_api = BybitAPIv5(
            api_key=BYBIT_API_KEY,
            secret_key=BYBIT_SECRET_KEY,
            testnet=USE_TESTNET
        )
        
        telegram_bot = TelegramBot(
            bot_token=TELEGRAM_BOT_TOKEN,
            chat_id=TELEGRAM_CHAT_ID
        )
        
        # Test API connection
        print("Testing Bybit API v5 connection...")
        btc_price = bybit_api.get_current_price("BTCUSDT")
        if btc_price:
            print(f"✅ API v5 working! BTC Price: ${btc_price:.2f}")
        else:
            print("❌ API v5 connection failed!")
            return
        
        # Test Telegram connection
        print("Testing Telegram bot...")
        test_message = "🤖 Trading Signals Bot Started!\n\nUsing Bybit API v5 ✅"
        if telegram_bot.send_message(test_message):
            print("✅ Telegram bot working!")
        else:
            print("❌ Telegram bot failed!")
            return
        
        # Initialize trading signals bot
        trading_bot = TradingSignalsBot(bybit_api, telegram_bot)
        
        # Get market summary
        summary = trading_bot.get_market_summary()
        print("\nMarket Summary:")
        print(summary.replace("<b>", "").replace("</b>", ""))
        
        # Start monitoring (uncomment to run continuous monitoring)
        # trading_bot.run_monitoring(
        #     symbols=["BTCUSDT", "ETHUSDT"],
        #     check_interval=60,
        #     price_threshold=1.0
        # )
        
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()