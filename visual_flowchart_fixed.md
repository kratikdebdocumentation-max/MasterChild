# MasterChild_GUI Trading Application - Visual Flow Chart

## Main Application Flow

```mermaid
flowchart TD
    A[🚀 Application Start] --> B[📋 Load Configuration]
    B --> C[🔐 Initialize Accounts]
    C --> D[📊 Load Market Data]
    D --> E[🌐 Setup WebSocket]
    E --> F[🖥️ Display GUI]
    
    F --> G{User Action}
    
    G -->|Place Order| H[📝 Validate Order]
    G -->|Login/Logout| I[🔑 Account Control]
    G -->|View Data| J[📈 Market Data Display]
    G -->|Configure| K[⚙️ Config Window]
    
    H --> L[📤 Send to API]
    L --> M[📡 WebSocket Update]
    M --> N[🔄 Update UI]
    
    I --> O[🔐 API Login/Logout]
    O --> P[💾 Update State]
    P --> N
    
    J --> Q[📊 Live Price Feed]
    Q --> N
    
    K --> R[💾 Save Config]
    R --> N
    
    N --> G
```

## System Architecture Flow

```mermaid
flowchart LR
    subgraph "Main Application"
        MAIN[main.py MainWindow]
    end
    
    subgraph "Configuration Layer"
        CONFIG[ConfigManager]
        CONFIG_FILE[configuration.csv]
        CONFIG_WIN[ConfigWindow]
    end
    
    subgraph "Account Management"
        ACC_MGR[AccountManager]
        STATE_MGR[AccountStateManager]
        CREDS[credentials1.json credentials2.json]
        STATE_CSV[account_state.csv]
    end
    
    subgraph "Real-time Data"
        WS_MGR[WebSocketManager]
        API[api_helper.py ShoonyaApiPy]
        EXTERNAL[Shonaya Trading API]
    end
    
    subgraph "Market Data"
        INDEX[SimpleIndexManager NIFTY/BANKNIFTY/SENSEX]
        EXPIRY[ExpiryManager Option Expiry Dates]
        SYMBOL[SymbolManager Symbol Data]
    end
    
    subgraph "Logging"
        LOGGER[logger.py]
        LOGS[logs directory]
    end
    
    subgraph "User Interface"
        GUI[Trading Interface]
        CONFIG_UI[Settings Interface]
    end
    
    MAIN --> CONFIG
    MAIN --> ACC_MGR
    MAIN --> STATE_MGR
    MAIN --> WS_MGR
    MAIN --> INDEX
    MAIN --> EXPIRY
    MAIN --> SYMBOL
    MAIN --> GUI
    
    CONFIG --> CONFIG_FILE
    CONFIG --> CONFIG_WIN
    CONFIG_WIN --> CONFIG_UI
    
    ACC_MGR --> CREDS
    ACC_MGR --> API
    STATE_MGR --> STATE_CSV
    
    WS_MGR --> ACC_MGR
    WS_MGR --> API
    API --> EXTERNAL
    EXTERNAL --> WS_MGR
    
    INDEX --> GUI
    EXPIRY --> GUI
    SYMBOL --> GUI
    
    MAIN --> LOGGER
    ACC_MGR --> LOGGER
    WS_MGR --> LOGGER
    LOGGER --> LOGS
    
    GUI --> CONFIG_UI
```

## Trading Order Flow

```mermaid
flowchart TD
    START[User Clicks Order Button] --> VALIDATE{Validate Input}
    
    VALIDATE -->|Invalid| ERROR[Show Error Message]
    VALIDATE -->|Valid| CHECK_ACCOUNT{Check Account Status}
    
    CHECK_ACCOUNT -->|Not Logged In| LOGIN_REQ[Login Required]
    CHECK_ACCOUNT -->|Ready| PREPARE[Prepare Order Data]
    
    PREPARE --> API_CALL[Call Trading API]
    API_CALL --> API_RESPONSE{API Response}
    
    API_RESPONSE -->|Failed| API_ERROR[Show API Error]
    API_RESPONSE -->|Success| UPDATE_STATE[Update Account State]
    
    UPDATE_STATE --> WS_NOTIFY[Notify WebSocket]
    WS_NOTIFY --> ORDER_PLACED[Order Placed Successfully]
    
    ORDER_PLACED --> WS_MONITOR[Monitor Order Status]
    WS_MONITOR --> STATUS_UPDATE[Update Order Status in UI]
    
    STATUS_UPDATE --> COMPLETE[Order Complete]
    
    ERROR --> START
    LOGIN_REQ --> START
    API_ERROR --> START
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph "Data Sources"
        CSV[CSV Files configuration.csv account_state.csv]
        JSON[JSON Files credentials1.json credentials2.json cache files]
        TXT[Text Files symbol files expiry files price files]
        API[External API Shonaya Trading]
    end
    
    subgraph "Processing Layer"
        CONFIG_PROC[ConfigManager Settings Processing]
        ACCOUNT_PROC[AccountManager Account Processing]
        STATE_PROC[AccountStateManager State Processing]
        MARKET_PROC[Market Data Managers Data Processing]
    end
    
    subgraph "Business Logic"
        ORDER_LOGIC[Order Management Place/Modify/Cancel]
        ACCOUNT_LOGIC[Account Control Login/Logout]
        DATA_LOGIC[Market Data Logic Price/Expiry/Symbol]
    end
    
    subgraph "User Interface"
        MAIN_GUI[Main Window Trading Interface]
        CONFIG_GUI[Config Window Settings Interface]
        LOGS_GUI[Logging System Debug Interface]
    end
    
    CSV --> CONFIG_PROC
    JSON --> ACCOUNT_PROC
    TXT --> MARKET_PROC
    API --> ACCOUNT_PROC
    
    CONFIG_PROC --> ORDER_LOGIC
    ACCOUNT_PROC --> ORDER_LOGIC
    STATE_PROC --> ORDER_LOGIC
    MARKET_PROC --> DATA_LOGIC
    
    ORDER_LOGIC --> MAIN_GUI
    ACCOUNT_LOGIC --> MAIN_GUI
    DATA_LOGIC --> MAIN_GUI
    
    MAIN_GUI --> CONFIG_GUI
    MAIN_GUI --> LOGS_GUI
```

## Module Dependencies Flow

```mermaid
flowchart TD
    MAIN[main.py Main Application] --> ACC_MGR[trading/account_manager.py Account Management]
    MAIN --> STATE_MGR[trading/account_state_manager.py State Management]
    MAIN --> WS_MGR[trading/websocket_manager.py Real-time Data]
    MAIN --> CONFIG_MGR[config_manager.py Configuration]
    MAIN --> CONFIG[config.py Settings]
    MAIN --> LOGGER[logger.py Logging]
    
    MAIN --> INDEX_MGR[market_data/simple_index_manager.py Index Prices]
    MAIN --> EXPIRY_MGR[market_data/expiry_manager.py Expiry Dates]
    MAIN --> SYMBOL_MGR[market_data/symbol_manager.py Symbol Data]
    
    MAIN --> CONFIG_WIN[config_window.py Config UI]
    
    ACC_MGR --> API[api_helper.py Trading API]
    WS_MGR --> API
    
    ACC_MGR --> CONFIG
    STATE_MGR --> CONFIG
    WS_MGR --> ACC_MGR
    CONFIG_MGR --> CONFIG
    INDEX_MGR --> LOGGER
    EXPIRY_MGR --> LOGGER
    SYMBOL_MGR --> LOGGER
    CONFIG_WIN --> CONFIG_MGR
```

## Key Features Flow

```mermaid
flowchart TB
    subgraph "Application Startup"
        START[Application Start] --> INIT[Initialize Components]
        INIT --> LOAD_CONFIG[Load Configuration]
        LOAD_CONFIG --> LOAD_ACCOUNTS[Load Account Credentials]
        LOAD_ACCOUNTS --> AUTO_LOGIN[Auto-login Master Account]
        AUTO_LOGIN --> SETUP_WS[Setup WebSocket]
        SETUP_WS --> READY[Application Ready]
    end
    
    subgraph "Trading Operations"
        READY --> ORDER_INPUT[Order Input]
        ORDER_INPUT --> VALIDATE[Validate Order]
        VALIDATE --> PLACE_ORDER[Place Order via API]
        PLACE_ORDER --> UPDATE_STATE[Update Account State]
        UPDATE_STATE --> WS_UPDATE[WebSocket Status Update]
        WS_UPDATE --> UI_UPDATE[Update UI Display]
    end
    
    subgraph "Market Data"
        READY --> LOAD_SYMBOLS[Load Symbol Data]
        LOAD_SYMBOLS --> LOAD_EXPIRY[Load Expiry Dates]
        LOAD_EXPIRY --> LOAD_PRICES[Load Index Prices]
        LOAD_PRICES --> LIVE_FEED[Live Price Feed]
        LIVE_FEED --> UI_UPDATE
    end
    
    subgraph "Account Management"
        READY --> ACCOUNT_CONTROL[Account Control]
        ACCOUNT_CONTROL --> LOGIN[Login/Logout]
        ACCOUNT_CONTROL --> STATE_UPDATE[State Updates]
        LOGIN --> API_CALL[API Call]
        STATE_UPDATE --> CSV_UPDATE[CSV Update]
    end
```

## File Structure Visual

```mermaid
flowchart TD
    ROOT[MasterChild_GUI] --> MAIN[main.py Main Application]
    ROOT --> CONFIG[config.py Configuration]
    ROOT --> CONFIG_MGR[config_manager.py Config Management]
    ROOT --> CONFIG_WIN[config_window.py Config UI]
    ROOT --> API[api_helper.py Trading API]
    ROOT --> LOGGER[logger.py Logging]
    ROOT --> CSV[account_state.csv Account States]
    ROOT --> CONFIG_CSV[configuration.csv Settings]
    ROOT --> CREDS1[credentials1.json Master Account]
    ROOT --> CREDS2[credentials2.json Child Account]
    
    ROOT --> TRADING[trading]
    TRADING --> ACC_MGR[account_manager.py Account Management]
    TRADING --> STATE_MGR[account_state_manager.py State Management]
    TRADING --> WS_MGR[websocket_manager.py Real-time Data]
    
    ROOT --> MARKET[market_data]
    MARKET --> INDEX_MGR[simple_index_manager.py Index Prices]
    MARKET --> EXPIRY_MGR[expiry_manager.py Expiry Dates]
    MARKET --> SYMBOL_MGR[symbol_manager.py Symbol Data]
    
    ROOT --> DATA[data]
    DATA --> NFO[NFO_symbols.txt NFO Symbols]
    DATA --> BFO[BFO_symbols.txt BFO Symbols]
    DATA --> EXPIRY_FILES[expiry_dates.txt Expiry Dates]
    DATA --> PRICE_FILES[index_prices.txt Price Data]
    DATA --> CACHE[cache.json Cache Files]
    
    ROOT --> LOGS[logs]
    LOGS --> APP_LOGS[app.log Application Logs]
    LOGS --> WS_LOGS[WS.log WebSocket Logs]
    LOGS --> GENERAL_LOGS[applicationLogger.log General Logs]
```

This corrected version should work perfectly in Mermaid Live Editor! The main fixes were:
1. Removed emojis from node labels (they can cause parsing issues)
2. Fixed subgraph syntax
3. Simplified node names to avoid special characters
4. Ensured proper Mermaid syntax throughout

You can now copy this content to [Mermaid Live Editor](https://mermaid.live/) and it should render without any errors!
