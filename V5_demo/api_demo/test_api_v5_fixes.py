#!/usr/bin/env python3
"""
Unit tests for Bybit API v5 fixes

Tests the core functionality of the fixed API methods
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading_signals_bot import BybitAPIv5, TelegramBot, TradingSignalsBot


class TestBybitAPIv5Fixes(unittest.TestCase):
    """Test the fixes for Bybit API v5 compatibility"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api = BybitAPIv5(
            api_key="test_key",
            secret_key="test_secret",
            testnet=True
        )
    
    def test_api_initialization(self):
        """Test that API initializes correctly"""
        self.assertEqual(self.api.api_key, "test_key")
        self.assertEqual(self.api.secret_key, "test_secret")
        self.assertEqual(self.api.base_url, "https://api-testnet.bybit.com")
        self.assertEqual(self.api.recv_window, 5000)
    
    def test_signature_generation(self):
        """Test HMAC signature generation"""
        timestamp = "1234567890000"
        payload = "category=spot&symbol=BTCUSDT"
        
        signature = self.api._generate_signature(timestamp, payload)
        
        # Should return a valid hex string
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex length
        # Verify it contains only valid hex characters
        self.assertTrue(all(c in '0123456789abcdef' for c in signature))
    
    @patch('requests.Session.get')
    def test_get_market_ticker_success(self, mock_get):
        """Test successful get_market_ticker call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [{
                    "symbol": "BTCUSDT",
                    "lastPrice": "45000.00",
                    "price24hPcnt": "2.5",
                    "volume24h": "12345.67"
                }]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.get_market_ticker("spot", "BTCUSDT")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["lastPrice"], "45000.00")
    
    @patch('requests.Session.get')
    def test_get_current_price_success(self, mock_get):
        """Test successful get_current_price call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [{
                    "symbol": "BTCUSDT",
                    "lastPrice": "45000.00"
                }]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        price = self.api.get_current_price("BTCUSDT")
        
        self.assertIsNotNone(price)
        self.assertEqual(price, 45000.00)
        self.assertIsInstance(price, float)
    
    @patch('requests.Session.get')
    def test_get_market_ticker_api_error(self, mock_get):
        """Test get_market_ticker with API error response"""
        # Mock API error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "retCode": 10001,
            "retMsg": "API key error"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.get_market_ticker("spot", "BTCUSDT")
        
        self.assertIsNone(result)
    
    @patch('requests.Session.get')
    def test_get_current_price_network_error(self, mock_get):
        """Test get_current_price with network error"""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        result = self.api.get_current_price("BTCUSDT")
        
        self.assertIsNone(result)
    
    def test_telegram_bot_initialization(self):
        """Test Telegram bot initialization"""
        bot = TelegramBot("test_token", "test_chat_id")
        
        self.assertEqual(bot.bot_token, "test_token")
        self.assertEqual(bot.chat_id, "test_chat_id")
        self.assertEqual(bot.base_url, "https://api.telegram.org/bottest_token")
    
    @patch('requests.post')
    def test_telegram_send_message_success(self, mock_post):
        """Test successful Telegram message sending"""
        bot = TelegramBot("test_token", "test_chat_id")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = bot.send_message("Test message")
        
        self.assertTrue(result)
    
    def test_trading_signals_bot_initialization(self):
        """Test trading signals bot initialization"""
        api = BybitAPIv5("key", "secret")
        telegram = TelegramBot("token", "chat")
        
        bot = TradingSignalsBot(api, telegram)
        
        self.assertEqual(bot.bybit_api, api)
        self.assertEqual(bot.telegram_bot, telegram)
        self.assertEqual(bot.last_prices, {})


class TestAPIv5Compatibility(unittest.TestCase):
    """Test that the fixes address the original issues"""
    
    def test_get_ticker_method_deprecated(self):
        """Verify that get_ticker method issue is addressed"""
        api = BybitAPIv5("key", "secret")
        
        # The old get_ticker method should not exist
        self.assertFalse(hasattr(api, 'get_ticker'))
        
        # The new get_market_ticker method should exist
        self.assertTrue(hasattr(api, 'get_market_ticker'))
        self.assertTrue(callable(getattr(api, 'get_market_ticker')))
    
    def test_get_current_price_exists(self):
        """Test that get_current_price method exists and is callable"""
        api = BybitAPIv5("key", "secret")
        
        self.assertTrue(hasattr(api, 'get_current_price'))
        self.assertTrue(callable(getattr(api, 'get_current_price')))
    
    def test_http_request_method_exists(self):
        """Test that HTTP request handling exists"""
        api = BybitAPIv5("key", "secret")
        
        # Should have a private method for making requests
        self.assertTrue(hasattr(api, '_make_request'))
        self.assertTrue(callable(getattr(api, '_make_request')))


def run_tests():
    """Run all tests and display results"""
    print("=" * 60)
    print("RUNNING BYBIT API v5 FIX TESTS")
    print("=" * 60)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - API v5 fixes are working correctly!")
    else:
        print("❌ Some tests failed - check the output above")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)