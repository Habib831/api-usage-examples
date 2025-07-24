"""
Example demonstrating the fix for Bybit API v5 compatibility

This script shows the BEFORE and AFTER for the API method changes:
- BEFORE: get_ticker() method (deprecated, causes AttributeError)  
- AFTER: get_market_ticker() method (API v5 compatible)

The main issue was that 'HTTP' object doesn't have 'get_ticker' attribute.
This has been fixed by using the correct API v5 endpoint and method.
"""

import requests
import time
import hashlib
import hmac
import json
import logging

# Configure logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BybitAPIFix:
    """
    Demonstrates the fix for Bybit API v5 compatibility issues
    """
    
    def __init__(self, api_key: str = "YOUR_API_KEY", secret_key: str = "YOUR_SECRET_KEY", testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.recv_window = 5000
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        self.session = requests.Session()
    
    def _generate_signature(self, timestamp: str, payload: str) -> str:
        """Generate HMAC signature for API v5"""
        param_str = f"{timestamp}{self.api_key}{self.recv_window}{payload}"
        return hmac.new(
            self.secret_key.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _http_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """
        HTTP request handler for API v5 
        Fixed version that works with current Bybit API
        """
        timestamp = str(int(time.time() * 1000))
        
        if method == "GET":
            query_string = "&".join([f"{k}={v}" for k, v in (params or {}).items()])
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
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            else:
                response = self.session.post(url, headers=headers, data=payload, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    # ❌ OLD METHOD (BROKEN) - This would cause AttributeError
    def get_ticker_old_way(self, symbol: str = "BTCUSDT"):
        """
        OLD WAY: This method demonstrates the broken approach
        The error: 'HTTP' object has no attribute 'get_ticker'
        """
        # This is what was causing the error:
        # return self.HTTP.get_ticker(symbol=symbol)  # ❌ AttributeError!
        
        print("❌ OLD WAY: get_ticker() method is deprecated and causes AttributeError")
        print("   Error: 'HTTP' object has no attribute 'get_ticker'")
        return None
    
    # ✅ NEW METHOD (FIXED) - Uses API v5 compatible endpoint
    def get_market_ticker(self, symbol: str = "BTCUSDT", category: str = "spot") -> dict:
        """
        NEW WAY: Fixed method using API v5 compatible endpoint
        Replaces the deprecated get_ticker() method
        """
        endpoint = "/v5/market/tickers"
        params = {
            "category": category,
            "symbol": symbol
        }
        
        print(f"✅ NEW WAY: Using get_market_ticker() with API v5 endpoint: {endpoint}")
        response = self._http_request("GET", endpoint, params)
        
        if response.get("retCode") == 0:
            result = response.get("result", {})
            ticker_list = result.get("list", [])
            if ticker_list:
                return ticker_list[0]
        
        return {}
    
    # ✅ FIXED get_current_price function
    def get_current_price(self, symbol: str = "BTCUSDT", category: str = "spot") -> float:
        """
        FIXED: get_current_price function now uses get_market_ticker
        This replaces any broken implementation that used get_ticker
        """
        print(f"✅ FIXED: get_current_price() now uses get_market_ticker() for {symbol}")
        
        ticker_data = self.get_market_ticker(symbol=symbol, category=category)
        
        if ticker_data and "lastPrice" in ticker_data:
            price = float(ticker_data["lastPrice"])
            print(f"   Current price for {symbol}: ${price:.4f}")
            return price
        else:
            print(f"   ❌ Could not get price for {symbol}")
            return 0.0


def demonstrate_fix():
    """
    Demonstrate the fix for the Bybit API v5 compatibility issue
    """
    print("=" * 60)
    print("BYBIT API v5 COMPATIBILITY FIX DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Initialize the fixed API client
    api = BybitAPIFix()
    
    print("🔧 ISSUE: 'HTTP' object has no attribute 'get_ticker'")
    print("🔧 SOLUTION: Use 'get_market_ticker' method with API v5 endpoints")
    print()
    
    # Show the old broken way
    print("1. OLD BROKEN METHOD:")
    print("-" * 30)
    api.get_ticker_old_way("BTCUSDT")
    print()
    
    # Show the new fixed way
    print("2. NEW FIXED METHOD:")  
    print("-" * 30)
    ticker_data = api.get_market_ticker("BTCUSDT", "spot")
    
    if ticker_data:
        print("   ✅ SUCCESS: get_market_ticker() returned data")
        print(f"   📊 Ticker data keys: {list(ticker_data.keys())}")
        
        # Extract key information
        if "lastPrice" in ticker_data:
            print(f"   💰 Last Price: {ticker_data['lastPrice']}")
        if "price24hPcnt" in ticker_data:
            print(f"   📈 24h Change: {ticker_data['price24hPcnt']}%")
        if "volume24h" in ticker_data:
            print(f"   📊 24h Volume: {ticker_data['volume24h']}")
    else:
        print("   ❌ No data returned (check API credentials)")
    
    print()
    
    # Demonstrate the fixed get_current_price function
    print("3. FIXED get_current_price() FUNCTION:")
    print("-" * 40)
    current_price = api.get_current_price("BTCUSDT")
    print()
    
    print("🎉 FIX SUMMARY:")
    print("-" * 20)
    print("✅ Replaced deprecated get_ticker() with get_market_ticker()")
    print("✅ Updated get_current_price() to use API v5 methods")
    print("✅ Added proper error handling")
    print("✅ Compatible with Bybit API v5")
    print()


if __name__ == "__main__":
    demonstrate_fix()