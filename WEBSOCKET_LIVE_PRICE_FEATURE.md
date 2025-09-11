# WebSocket Live Price Feature

## Overview
This feature adds real-time price updates to the Master-Child Trading GUI System. When the "Fetch Price" button is pressed, the system now:

1. Fetches the current LTP (Last Traded Price) and populates the price boxes
2. Subscribes to the websocket feed for live price updates
3. Displays live price updates in the "Premium Price" box

## Implementation Details

### Files Modified
- `gui/main_window.py` - Added live price display and websocket subscription logic
- `trading/websocket_manager.py` - Enhanced to handle live price callbacks

### Key Components

#### 1. Premium Price Display
- Added a new readonly text box labeled "Premium Price" in the login frame
- This box shows live price updates from the websocket feed
- Initially populated with the fetched LTP when "Fetch Price" is pressed

#### 2. WebSocket Subscription
- When "Fetch Price" is pressed, the system automatically subscribes to the websocket feed
- Subscription format: `{exchange}|{token}` (e.g., "NSE|26000", "BFO|12345")
- Automatically unsubscribes from previous subscription when switching symbols

#### 3. Live Price Updates
- WebSocket feed receives data with `lp` field containing the latest price
- Live price is automatically updated in the "Premium Price" box
- Price is formatted to 2 decimal places

### Usage
1. Select your trading instrument (Index, Expiry, Strike, Option)
2. Click "Fetch Price" button
3. The system will:
   - Fetch and display the current LTP in all price boxes
   - Subscribe to live price feed
   - Start showing live price updates in the "Premium Price" box

### Technical Details

#### WebSocket API Format
```python
# Subscribe to symbol
api.subscribe('NSE|26000')  # For NSE symbols
api.subscribe('BFO|12345')  # For BFO (SENSEX) symbols

# WebSocket data format
{
    'e': 'NSE',      # Exchange
    'tk': '26000',   # Token
    'lp': '24500.50', # Last Traded Price
    'pc': '0.25',    # Percentage change
    'v': '1000',     # Volume
    # ... other fields
}
```

#### Exchange Mapping
- NIFTY, BANKNIFTY options → NFO exchange
- SENSEX options → BFO exchange

### Error Handling
- Graceful handling of websocket connection issues
- Automatic unsubscription from previous symbols
- Error logging for debugging
- Fallback to static price if websocket fails

### Logging
All websocket activities are logged using the application logger:
- Subscription/unsubscription events
- Live price updates (debug level)
- Error conditions

## Benefits
1. **Real-time Updates**: Users can see live price changes without manual refresh
2. **Better Trading Decisions**: Live price helps in making timely trading decisions
3. **Seamless Integration**: Works with existing fetch price functionality
4. **Automatic Management**: Handles subscription/unsubscription automatically
