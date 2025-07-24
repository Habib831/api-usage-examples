#!/usr/bin/env python3
"""
Test script for Bybit Telegram Bot functionality.

This script tests the key components of the bot without requiring full
environment setup or making actual API calls during testing.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the current directory to path to import the bot module
sys.path.append(os.path.dirname(__file__))

from bybit_telegram_bot import BybitTelegramBot


class TestBybitTelegramBot(unittest.TestCase):
    """Test cases for the BybitTelegramBot class."""
    
    def setUp(self):
        """Set up test environment variables."""
        self.test_env = {
            'BYBIT_API_KEY': 'test_api_key',
            'BYBIT_API_SECRET': 'test_api_secret',
            'TELEGRAM_BOT_TOKEN': 'test_bot_token',
            'TELEGRAM_CHAT_ID': 'test_chat_id',
            'SYMBOL': 'BTCUSDT',
            'UPDATE_INTERVAL': '60'
        }
        
        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, self.test_env)
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    @patch('bybit_telegram_bot.HTTP')
    def test_bot_initialization_success(self, mock_http):
        """Test successful bot initialization."""
        mock_http.return_value = Mock()
        
        bot = BybitTelegramBot()
        
        self.assertEqual(bot.api_key, 'test_api_key')
        self.assertEqual(bot.api_secret, 'test_api_secret')
        self.assertEqual(bot.telegram_token, 'test_bot_token')
        self.assertEqual(bot.chat_id, 'test_chat_id')
        self.assertEqual(bot.symbol, 'BTCUSDT')
        self.assertEqual(bot.update_interval, 60)
    
    def test_bot_initialization_missing_config(self):
        """Test bot initialization with missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                BybitTelegramBot()
            
            self.assertIn("Missing required environment variables", str(context.exception))
    
    @patch('bybit_telegram_bot.HTTP')
    def test_get_current_price_success(self, mock_http):
        """Test successful price retrieval."""
        # Setup mock response
        mock_session = Mock()
        mock_session.get_tickers.return_value = {
            'result': {
                'list': [{'lastPrice': '50000.1234'}]
            }
        }
        mock_http.return_value = mock_session
        
        bot = BybitTelegramBot()
        price = bot.get_current_price('BTCUSDT')
        
        self.assertEqual(price, 50000.1234)
        mock_session.get_tickers.assert_called_once_with(category="spot", symbol='BTCUSDT')
    
    @patch('bybit_telegram_bot.HTTP')
    def test_get_current_price_list_response(self, mock_http):
        """Test price retrieval with multiple ticker data."""
        # Setup mock response with multiple tickers
        mock_session = Mock()
        mock_session.get_tickers.return_value = {
            'result': {
                'list': [
                    {'lastPrice': '45000.5678'},
                    {'lastPrice': '46000.0000'}  # Should use first one
                ]
            }
        }
        mock_http.return_value = mock_session
        
        bot = BybitTelegramBot()
        price = bot.get_current_price('BTCUSDT')
        
        self.assertEqual(price, 45000.5678)
    
    @patch('bybit_telegram_bot.HTTP')
    def test_get_current_price_api_error(self, mock_http):
        """Test price retrieval with API error."""
        mock_session = Mock()
        mock_session.get_tickers.side_effect = Exception("API Error")
        mock_http.return_value = mock_session
        
        bot = BybitTelegramBot()
        price = bot.get_current_price('BTCUSDT')
        
        self.assertIsNone(price)
    
    @patch('bybit_telegram_bot.HTTP')
    def test_get_current_price_invalid_response(self, mock_http):
        """Test price retrieval with invalid response."""
        mock_session = Mock()
        mock_session.get_tickers.return_value = {'invalid': 'response'}
        mock_http.return_value = mock_session
        
        bot = BybitTelegramBot()
        price = bot.get_current_price('BTCUSDT')
        
        self.assertIsNone(price)
    
    @patch('bybit_telegram_bot.HTTP')
    @patch('bybit_telegram_bot.requests.post')
    def test_send_telegram_message_success(self, mock_post, mock_http):
        """Test successful Telegram message sending."""
        mock_http.return_value = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        bot = BybitTelegramBot()
        result = bot.send_telegram_message("Test message")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('bybit_telegram_bot.HTTP')
    @patch('bybit_telegram_bot.requests.post')
    def test_send_telegram_message_api_error(self, mock_post, mock_http):
        """Test Telegram message sending with API error."""
        mock_http.return_value = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {'ok': False, 'description': 'API Error'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        bot = BybitTelegramBot()
        result = bot.send_telegram_message("Test message")
        
        self.assertFalse(result)
    
    @patch('bybit_telegram_bot.HTTP')
    def test_format_price_message(self, mock_http):
        """Test price message formatting."""
        mock_http.return_value = Mock()
        
        bot = BybitTelegramBot()
        message = bot.format_price_message('BTCUSDT', 50000.1234)
        
        self.assertIn('BTCUSDT', message)
        self.assertIn('50,000.1234', message)
        self.assertIn('Price Update', message)
        self.assertIn('🔄', message)  # Check for emoji


class TestIntegration(unittest.TestCase):
    """Integration tests for the bot functionality."""
    
    def setUp(self):
        """Set up test environment variables."""
        self.test_env = {
            'BYBIT_API_KEY': 'test_api_key',
            'BYBIT_API_SECRET': 'test_api_secret',
            'TELEGRAM_BOT_TOKEN': 'test_bot_token',
            'TELEGRAM_CHAT_ID': 'test_chat_id'
        }
        
        self.env_patcher = patch.dict(os.environ, self.test_env)
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    @patch('bybit_telegram_bot.HTTP')
    @patch('bybit_telegram_bot.requests.post')
    @patch('bybit_telegram_bot.time.sleep')  # Mock sleep to speed up tests
    def test_full_workflow(self, mock_sleep, mock_post, mock_http):
        """Test the complete workflow from price fetch to message send."""
        # Setup mocks
        mock_session = Mock()
        mock_session.get_tickers.return_value = {
            'result': {
                'list': [{'lastPrice': '50000.0000'}]
            }
        }
        mock_http.return_value = mock_session
        
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create bot and simulate one iteration
        bot = BybitTelegramBot()
        
        # Test individual components
        price = bot.get_current_price('BTCUSDT')
        self.assertEqual(price, 50000.0)
        
        message = bot.format_price_message('BTCUSDT', price)
        self.assertIn('50,000.0000', message)
        
        result = bot.send_telegram_message(message)
        self.assertTrue(result)


def run_tests():
    """Run all tests."""
    print("Running Bybit Telegram Bot tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBybitTelegramBot))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)