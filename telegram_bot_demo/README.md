# Bybit API to Telegram Bot Demo

This demo showcases how to create a bot that fetches cryptocurrency prices from the Bybit API and sends updates to a Telegram chat. The script has been enhanced with better error handling, logging, modularity, and compatibility with older versions of the Bybit API.

## Features

- ✅ **API Compatibility**: Uses `get_ticker` method for compatibility with older Bybit API versions
- ✅ **Comprehensive Error Handling**: Robust error handling for API calls and network issues
- ✅ **Logging**: Detailed logging to both file and console for debugging and monitoring
- ✅ **Modular Design**: Object-oriented approach for better code organization
- ✅ **Retry Logic**: Automatic retry for failed network requests with exponential backoff
- ✅ **Configuration**: Easy configuration via environment variables
- ✅ **Message Formatting**: Rich HTML-formatted messages with timestamps

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```env
# Bybit API Configuration
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_API_SECRET=your_bybit_api_secret_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Optional Settings
SYMBOL=BTCUSDT
UPDATE_INTERVAL=60
```

### 3. Get Required Credentials

#### Bybit API Credentials:
1. Go to [Bybit API Management](https://www.bybit.com/app/user/api-management)
2. Create a new API key
3. Copy the API Key and API Secret

#### Telegram Bot Token:
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token provided

#### Telegram Chat ID:
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your chat ID from the response

### 4. Run the Bot

```bash
python bybit_telegram_bot.py
```

## Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BYBIT_API_KEY` | Your Bybit API key | - | Yes |
| `BYBIT_API_SECRET` | Your Bybit API secret | - | Yes |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | - | Yes |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | - | Yes |
| `SYMBOL` | Trading pair to monitor | BTCUSDT | No |
| `UPDATE_INTERVAL` | Update interval in seconds | 60 | No |

## Key Improvements Made

### 1. API Method Compatibility
- **Before**: Used `get_market_ticker()` which is not supported in older Bybit API versions
- **After**: Uses `get_ticker()` method for better compatibility

### 2. Error Handling
- **Before**: Basic try/catch with no logging or specific error handling
- **After**: Comprehensive error handling for different types of failures:
  - API response validation
  - Network timeouts and connection errors
  - Data parsing errors
  - Consecutive error tracking

### 3. Logging System
- **Before**: No logging at all
- **After**: Comprehensive logging system:
  - File logging (`telegram_bot.log`)
  - Console output
  - Different log levels (DEBUG, INFO, WARNING, ERROR)
  - Structured log messages with timestamps

### 4. Code Organization
- **Before**: Single script with global variables
- **After**: Object-oriented design with:
  - `BybitTelegramBot` class for encapsulation
  - Separate methods for different functionalities
  - Type hints for better code documentation
  - Comprehensive docstrings

### 5. Network Reliability
- **Before**: No retry logic for failed requests
- **After**: Retry mechanism with:
  - Exponential backoff
  - Timeout handling
  - Connection error recovery
  - Maximum retry limits

### 6. Message Enhancement
- **Before**: Plain text messages
- **After**: Rich HTML-formatted messages with:
  - Emojis and formatting
  - Timestamps
  - Better price formatting

## Monitoring and Logs

The bot creates a log file (`telegram_bot.log`) that contains detailed information about:
- Bot startup and configuration
- Price fetch attempts and results
- Telegram message delivery status
- Error occurrences and retry attempts
- Bot shutdown events

## Error Recovery

The bot includes several error recovery mechanisms:
- **Consecutive Error Tracking**: Stops after too many consecutive failures
- **Network Retry Logic**: Retries failed network requests with exponential backoff
- **API Response Validation**: Validates API response structure before processing
- **Graceful Shutdown**: Handles interruption signals properly

## Security Considerations

- Store sensitive credentials in environment variables, not in code
- Use the provided `.env.example` as a template
- Never commit your actual `.env` file to version control
- Consider using read-only API keys for price monitoring

## Troubleshooting

### Common Issues:

1. **"Missing required environment variables"**
   - Ensure all required variables are set in your `.env` file

2. **"Invalid API response structure"**
   - Check your Bybit API credentials
   - Verify the trading pair symbol exists

3. **"Failed to send Telegram message"**
   - Verify your Telegram bot token and chat ID
   - Ensure the bot has permission to send messages to the chat

4. **"Too many consecutive errors"**
   - Check network connectivity
   - Verify API credentials are still valid
   - Check Bybit API status

## License

This demo is part of the Bybit API usage examples repository and follows the same licensing terms.