# 🎮 Stream-Automator

**Automatic game detection and real-time stream updates for Twitch and Kick**

---

## 🚀 Live Version

**For a fully already connected version with 5-minute setup tutorial:**
🔗 **https://kainanteh.es/**

---

## 🛠️ Self-Hosting Configuration

If you want do it yourself :

```python
# Server Configuration
SERVIDOR_BASE = "http://localhost:3000"
SERVIDOR_SHEETS = "http://localhost:3000"

# Callback URLs
TWITCH_CALLBACK = "http://localhost:3000/twitch/callback"
KICK_CALLBACK = "http://localhost:3000/kick/callback"

# API Endpoints
TWITCH_AUTH = f"{SERVIDOR_BASE}/twitch/auth"
TWITCH_SET_USER = f"{SERVIDOR_BASE}/api/twitch/set_user_id"
TWITCH_UPDATE = f"{SERVIDOR_BASE}/api/twitch/update_stream"
KICK_AUTH = f"{SERVIDOR_SHEETS}/auth/kick"
KICK_SET_USER = f"{SERVIDOR_SHEETS}/api/set_user_id"
KICK_UPDATE = f"{SERVIDOR_SHEETS}/api/update_stream"
SHEET_CONFIG = f"{SERVIDOR_SHEETS}/api/get_sheet_config"

# Features
# - Automatic window/game detection
# - Real-time Twitch & Kick stream updates
# - Google Sheets integration
# - Scene-based activation system
# - Debounce timer optimization

# Setup Workflow
# 1. Configure local server with above endpoints
# 2. Set up Twitch/Kick apps with callback URLs
# 3. Install OBS script and connect accounts
# 4. Configure Google Sheets for game titles/categories
# 5. Start streaming with automatic updates

# Quick Deployment
# For fully already connected visit: https://kainanteh.es/
