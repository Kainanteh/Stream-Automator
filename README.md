# Stream-Automator-Pro
Automatic game detection and real-time updates for Twitch and Kick


Would work perfectly if you configure localhost and the callbacks correctly for both Twitch and Kick. Here's how:

✅ Functionality with Localhost
🔧 Required Configuration:
Local server:

python
SERVIDOR_BASE = "http://localhost:3000"    # or your preferred port
SERVIDOR_SHEETS = "http://localhost:3000"  # same server
Twitch App Callbacks:

text
http://localhost:3000/twitch/callback
Kick App Callbacks:

text
http://localhost:3000/kick/callback
🚀 Flow that WOULD work:
Twitch Connection:

"Connect with Twitch" button → http://localhost:3000/twitch/auth

Twitch redirects to localhost:3000/twitch/callback with code

Local server exchanges code for token

User copies user_code and pastes it in OBS

Kick Connection:

Same process with Kick endpoints

Automatic Detection:

Script detects windows/games

Queries Google Sheets via your local server

Updates stream on Twitch/Kick through APIs

🔍 Endpoints the script needs:
python
# Twitch endpoints
f"{SERVIDOR_BASE}/twitch/auth"                    # Start auth
f"{SERVIDOR_BASE}/api/twitch/set_user_id"         # Verify user  
f"{SERVIDOR_BASE}/api/twitch/update_stream"       # Update stream

# Kick endpoints  
f"{SERVIDOR_SHEETS}/auth/kick"                    # Start auth
f"{SERVIDOR_SHEETS}/api/set_user_id"              # Verify user
f"{SERVIDOR_SHEETS}/api/update_stream"            # Update stream

# Google Sheets
f"{SERVIDOR_SHEETS}/api/get_sheet_config"         # G
