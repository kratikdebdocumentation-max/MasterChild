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
    subgraph "🎯 Main Application"
        MAIN[main.py<br/>MainWindow]
    end
    
    subgraph "🔧 Configuration Layer"
        CONFIG[ConfigManager]
        CONFIG_FILE[configuration.csv]
        CONFIG_WIN[ConfigWindow]
    end
    
    subgraph "👥 Account Management"
        ACC_MGR[AccountManager]
        STATE_MGR[AccountStateManager]
        CREDS[credentials1.json<br/>credentials2.json]
        STATE_CSV[account_state.csv]
    end
    
    subgraph "📡 Real-time Data"
        WS_MGR[WebSocketManager]
        API[api_helper.py<br/>ShoonyaApiPy]
        EXTERNAL[Shonaya Trading API]
    end
    
    subgraph "📊 Market Data"
        INDEX[SimpleIndexManager<br/>NIFTY/BANKNIFTY/SENSEX]
        EXPIRY[ExpiryManager<br/>Option Expiry Dates]
        SYMBOL[SymbolManager<br/>Symbol Data]
    end
    
    subgraph "📝 Logging"
        LOGGER[logger.py]
        LOGS[logs/ directory]
    end
    
    subgraph "🖥️ User Interface"
        GUI[Trading Interface]
        CONFIG_UI[Settings Interface]
    end
    
    %% Main connections
    MAIN --> CONFIG
    MAIN --> ACC_MGR
    MAIN --> STATE_MGR
    MAIN --> WS_MGR
    MAIN --> INDEX
    MAIN --> EXPIRY
    MAIN --> SYMBOL
    MAIN --> GUI
    
    %% Configuration flow
    CONFIG --> CONFIG_FILE
    CONFIG --> CONFIG_WIN
    CONFIG_WIN --> CONFIG_UI
    
    %% Account flow
    ACC_MGR --> CREDS
    ACC_MGR --> API
    STATE_MGR --> STATE_CSV
    
    %% WebSocket flow
    WS_MGR --> ACC_MGR
    WS_MGR --> API
    API --> EXTERNAL
    EXTERNAL --> WS_MGR
    
    %% Market data flow
    INDEX --> GUI
    EXPIRY --> GUI
    SYMBOL --> GUI
    
    %% Logging flow
    MAIN --> LOGGER
    ACC_MGR --> LOGGER
    WS_MGR --> LOGGER
    LOGGER --> LOGS
    
    %% UI flow
    GUI --> CONFIG_UI
```

## Trading Order Flow

```mermaid
flowchart TD
    START[👤 User Clicks Order Button] --> VALIDATE{✅ Validate Input}
    
    VALIDATE -->|❌ Invalid| ERROR[❌ Show Error Message]
    VALIDATE -->|✅ Valid| CHECK_ACCOUNT{🔍 Check Account Status}
    
    CHECK_ACCOUNT -->|❌ Not Logged In| LOGIN_REQ[🔐 Login Required]
    CHECK_ACCOUNT -->|✅ Ready| PREPARE[📋 Prepare Order Data]
    
    PREPARE --> API_CALL[📡 Call Trading API]
    API_CALL --> API_RESPONSE{📨 API Response}
    
    API_RESPONSE -->|❌ Failed| API_ERROR[❌ Show API Error]
    API_RESPONSE -->|✅ Success| UPDATE_STATE[💾 Update Account State]
    
    UPDATE_STATE --> WS_NOTIFY[📡 Notify WebSocket]
    WS_NOTIFY --> ORDER_PLACED[✅ Order Placed Successfully]
    
    ORDER_PLACED --> WS_MONITOR[👀 Monitor Order Status]
    WS_MONITOR --> STATUS_UPDATE[📊 Update Order Status in UI]
    
    STATUS_UPDATE --> COMPLETE[✅ Order Complete]
    
    ERROR --> START
    LOGIN_REQ --> START
    API_ERROR --> START
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph "📥 Data Sources"
        CSV[CSV Files<br/>📄 configuration.csv<br/>📄 account_state.csv]
        JSON[JSON Files<br/>🔐 credentials1.json<br/>🔐 credentials2.json<br/>💾 cache files]
        TXT[Text Files<br/>📊 symbol files<br/>📅 expiry files<br/>💰 price files]
        API[External API<br/>🌐 Shonaya Trading]
    end
    
    subgraph "⚙️ Processing Layer"
        CONFIG_PROC[ConfigManager<br/>⚙️ Settings Processing]
        ACCOUNT_PROC[AccountManager<br/>👥 Account Processing]
        STATE_PROC[AccountStateManager<br/>📊 State Processing]
        MARKET_PROC[Market Data Managers<br/>📈 Data Processing]
    end
    
    subgraph "🧠 Business Logic"
        ORDER_LOGIC[Order Management<br/>📝 Place/Modify/Cancel]
        ACCOUNT_LOGIC[Account Control<br/>🔐 Login/Logout]
        DATA_LOGIC[Market Data Logic<br/>💰 Price/Expiry/Symbol]
    end
    
    subgraph "🖥️ User Interface"
        MAIN_GUI[Main Window<br/>📱 Trading Interface]
        CONFIG_GUI[Config Window<br/>⚙️ Settings Interface]
        LOGS_GUI[Logging System<br/>📝 Debug Interface]
    end
    
    %% Data flow arrows
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
    MAIN[main.py<br/>🎯 Main Application] --> ACC_MGR[trading/account_manager.py<br/>👥 Account Management]
    MAIN --> STATE_MGR[trading/account_state_manager.py<br/>📊 State Management]
    MAIN --> WS_MGR[trading/websocket_manager.py<br/>📡 Real-time Data]
    MAIN --> CONFIG_MGR[config_manager.py<br/>⚙️ Configuration]
    MAIN --> CONFIG[config.py<br/>🔧 Settings]
    MAIN --> LOGGER[logger.py<br/>📝 Logging]
    
    %% Market Data Modules
    MAIN --> INDEX_MGR[market_data/simple_index_manager.py<br/>📈 Index Prices]
    MAIN --> EXPIRY_MGR[market_data/expiry_manager.py<br/>📅 Expiry Dates]
    MAIN --> SYMBOL_MGR[market_data/symbol_manager.py<br/>📊 Symbol Data]
    
    %% Configuration
    MAIN --> CONFIG_WIN[config_window.py<br/>⚙️ Config UI]
    
    %% API Layer
    ACC_MGR --> API[api_helper.py<br/>🌐 Trading API]
    WS_MGR --> API
    
    %% Dependencies
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
    subgraph "🚀 Application Startup"
        START[Application Start] --> INIT[Initialize Components]
        INIT --> LOAD_CONFIG[Load Configuration]
        LOAD_CONFIG --> LOAD_ACCOUNTS[Load Account Credentials]
        LOAD_ACCOUNTS --> AUTO_LOGIN[Auto-login Master Account]
        AUTO_LOGIN --> SETUP_WS[Setup WebSocket]
        SETUP_WS --> READY[Application Ready]
    end
    
    subgraph "📝 Trading Operations"
        READY --> ORDER_INPUT[Order Input]
        ORDER_INPUT --> VALIDATE[Validate Order]
        VALIDATE --> PLACE_ORDER[Place Order via API]
        PLACE_ORDER --> UPDATE_STATE[Update Account State]
        UPDATE_STATE --> WS_UPDATE[WebSocket Status Update]
        WS_UPDATE --> UI_UPDATE[Update UI Display]
    end
    
    subgraph "📊 Market Data"
        READY --> LOAD_SYMBOLS[Load Symbol Data]
        LOAD_SYMBOLS --> LOAD_EXPIRY[Load Expiry Dates]
        LOAD_EXPIRY --> LOAD_PRICES[Load Index Prices]
        LOAD_PRICES --> LIVE_FEED[Live Price Feed]
        LIVE_FEED --> UI_UPDATE
    end
    
    subgraph "👥 Account Management"
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
    ROOT[📁 MasterChild_GUI/] --> MAIN[📄 main.py<br/>🎯 Main Application]
    ROOT --> CONFIG[📄 config.py<br/>⚙️ Configuration]
    ROOT --> CONFIG_MGR[📄 config_manager.py<br/>🔧 Config Management]
    ROOT --> CONFIG_WIN[📄 config_window.py<br/>⚙️ Config UI]
    ROOT --> API[📄 api_helper.py<br/>🌐 Trading API]
    ROOT --> LOGGER[📄 logger.py<br/>📝 Logging]
    ROOT --> CSV[📄 account_state.csv<br/>📊 Account States]
    ROOT --> CONFIG_CSV[📄 configuration.csv<br/>⚙️ Settings]
    ROOT --> CREDS1[📄 credentials1.json<br/>🔐 Master Account]
    ROOT --> CREDS2[📄 credentials2.json<br/>🔐 Child Account]
    
    ROOT --> TRADING[📁 trading/]
    TRADING --> ACC_MGR[📄 account_manager.py<br/>👥 Account Management]
    TRADING --> STATE_MGR[📄 account_state_manager.py<br/>📊 State Management]
    TRADING --> WS_MGR[📄 websocket_manager.py<br/>📡 Real-time Data]
    
    ROOT --> MARKET[📁 market_data/]
    MARKET --> INDEX_MGR[📄 simple_index_manager.py<br/>📈 Index Prices]
    MARKET --> EXPIRY_MGR[📄 expiry_manager.py<br/>📅 Expiry Dates]
    MARKET --> SYMBOL_MGR[📄 symbol_manager.py<br/>📊 Symbol Data]
    
    ROOT --> DATA[📁 data/]
    DATA --> NFO[📄 NFO_symbols.txt_*.txt<br/>📊 NFO Symbols]
    DATA --> BFO[📄 BFO_symbols.txt_*.txt<br/>📊 BFO Symbols]
    DATA --> EXPIRY_FILES[📄 *_expiry_dates.txt<br/>📅 Expiry Dates]
    DATA --> PRICE_FILES[📄 index_prices*.txt<br/>💰 Price Data]
    DATA --> CACHE[📄 *_cache.json<br/>💾 Cache Files]
    
    ROOT --> LOGS[📁 logs/]
    LOGS --> APP_LOGS[📄 app_*.log<br/>📝 Application Logs]
    LOGS --> WS_LOGS[📄 Log_*_WS_*.log<br/>📡 WebSocket Logs]
    LOGS --> GENERAL_LOGS[📄 applicationLogger_*.log<br/>📝 General Logs]
```

This visual flowchart shows the complete flow of your MasterChild_GUI trading application with clear visual indicators and emojis to make it easy to understand the relationships between different components!
