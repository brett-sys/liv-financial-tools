#!/bin/bash
# Call Logger Startup Script
# Starts the Flask server + Cloudflare tunnel together
# Writes the public URL to Google Sheets so Kevin always has it

PROJECT_DIR="/Users/dunham/Desktop/python"
APP_DIR="$PROJECT_DIR/call_logger"
VENV="$PROJECT_DIR/venv/bin/activate"
PORT=5055
URL_FILE="$APP_DIR/tunnel_url.txt"

# Kill any existing instances
lsof -ti :$PORT | xargs kill -9 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

# Verify port is actually free before proceeding
for i in $(seq 1 10); do
    lsof -ti :$PORT >/dev/null 2>&1 || break
    lsof -ti :$PORT | xargs kill -9 2>/dev/null
    sleep 1
done

if lsof -ti :$PORT >/dev/null 2>&1; then
    echo "ERROR: Port $PORT still in use after cleanup. Stale PIDs:"
    lsof -i :$PORT
    exit 1
fi

# Start Flask server
cd "$APP_DIR"
source "$VENV"
python -c "
from app import app
import scheduler
app.run(host='0.0.0.0', port=$PORT, debug=False)
" > "$APP_DIR/app.log" 2>&1 &
SERVER_PID=$!

# Wait for server
for i in $(seq 1 20); do
    curl -s -o /dev/null http://127.0.0.1:$PORT/ 2>/dev/null && break
    sleep 0.5
done

# Start Cloudflare tunnel and capture URL
cloudflared tunnel --url http://localhost:$PORT 2>&1 | while read line; do
    echo "$line"
    # Extract the tunnel URL (exclude api.trycloudflare.com from error messages)
    if echo "$line" | grep -q "trycloudflare.com" && ! echo "$line" | grep -q "api.trycloudflare.com"; then
        URL=$(echo "$line" | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com')
        if [ -n "$URL" ]; then
            echo "$URL" > "$URL_FILE"
            echo ""
            echo "========================================="
            echo "  Brett's link:    ${URL}/brett"
            echo "  Kevin's link:    ${URL}/kevin"
            echo "  Easton's link:   ${URL}/easton"
            echo "  Joe's link:      ${URL}/joe"
            echo "  Kooper's link:   ${URL}/kooper"
            echo "  Kaiden's link:   ${URL}/kaiden"
            echo "  Alex's link:     ${URL}/alex"
            echo "  Pedro's link:    ${URL}/pedro"
            echo "  Quavo's link:    ${URL}/quavo"
            echo "  Mahan's link:    ${URL}/mahan"
            echo "  Deven's link:    ${URL}/deven"
            echo "  Carmello's link: ${URL}/carmello"
            echo "  Daniel's link:   ${URL}/daniel"
            echo "  Manuel's link:   ${URL}/manuel"
            echo "  Nico's link:     ${URL}/nico"
            echo "  Jean's link:     ${URL}/jean"
            echo "========================================="
            echo ""
            # Update Google Sheet with the URLs
            cd "$APP_DIR"
            source "$VENV"
            python -c "
import gspread
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
import config
sheet = client.open_by_key(config.CALL_LOG_SHEET_ID)

def update_link_tab(sheet, tab_name, agent_name, url):
    try:
        info = sheet.worksheet(tab_name)
    except:
        info = sheet.add_worksheet(title=tab_name, rows=5, cols=2)
    info.clear()
    info.update([[f'{agent_name}\\'s Call Logger Link',''], [url,''], ['',''], ['Bookmark this sheet - the link updates automatically.','']])
    info.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})
    info.format('A2', {'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColorStyle': {'rgbColor': {'red': 0.06, 'green': 0.52, 'blue': 0.94}}}})

update_link_tab(sheet, 'Brett Link', 'Brett', '${URL}/brett')
update_link_tab(sheet, 'Kevin Link', 'Kevin', '${URL}/kevin')
update_link_tab(sheet, 'Easton Link', 'Easton', '${URL}/easton')
update_link_tab(sheet, 'Joe Link', 'Joe', '${URL}/joe')
update_link_tab(sheet, 'Kooper Link', 'Kooper', '${URL}/kooper')
update_link_tab(sheet, 'Kaiden Link', 'Kaiden', '${URL}/kaiden')
update_link_tab(sheet, 'Alex Link', 'Alex', '${URL}/alex')
update_link_tab(sheet, 'Pedro Link', 'Pedro', '${URL}/pedro')
update_link_tab(sheet, 'Quavo Link', 'Quavo', '${URL}/quavo')
update_link_tab(sheet, 'Mahan Link', 'Mahan', '${URL}/mahan')
update_link_tab(sheet, 'Deven Link', 'Deven', '${URL}/deven')
update_link_tab(sheet, 'Carmello Link', 'Carmello', '${URL}/carmello')
update_link_tab(sheet, 'Daniel Link', 'Daniel', '${URL}/daniel')
update_link_tab(sheet, 'Manuel Link', 'Manuel', '${URL}/manuel')
update_link_tab(sheet, 'Nico Link', 'Nico', '${URL}/nico')
update_link_tab(sheet, 'Jean Link', 'Jean', '${URL}/jean')
print('Google Sheet updated with all agent links')
" 2>&1 &
        fi
    fi
done

wait $SERVER_PID
