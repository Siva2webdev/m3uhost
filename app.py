import requests
from urllib.parse import urlparse, parse_qs
import time
from flask import Flask, render_template, request
from colorama import init, Fore
import sys

# Initialize colorama
init(autoreset=True)

# Ensure the output encoding is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# Headers for requests
headers = {
    "Cookie": "stb_lang=en; timezone=Europe%2FIstanbul;",
    "X-User-Agent": "Model: MAG254; Link: Ethernet",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json,application/javascript,text/javascript,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "VLC,Mozilla/5.0"
}

def fetch_url(session, url):
    try:
        response = session.get(url, headers=headers, timeout=3, verify=False)
        response.raise_for_status()  # Raise HTTPError for bad responses
        if response.headers['Content-Type'] == 'application/json':
            return response.json()
        else:
            return response.text
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def verificar_status_m3u(link_m3u):
    try:
        parsed_url = urlparse(link_m3u)
        query_params = parse_qs(parsed_url.query)
        full_url = parsed_url.scheme + "://" + parsed_url.netloc
        usuario = query_params.get('username', [None])[0]
        senha = query_params.get('password', [None])[0]

        if not usuario or not senha:
            return "Invalid URL: Missing username or password", None, None, None, None, None, None, None

        link = f"{full_url}/player_api.php?username={usuario}&password={senha}&type=m3u"
        liveurl = f"{full_url}/player_api.php?username={usuario}&password={senha}&action=get_live_categories"
        vodurl = f"{full_url}/player_api.php?username={usuario}&password={senha}&action=get_vod_categories"
        seriesurl = f"{full_url}/player_api.php?username={usuario}&password={senha}&action=get_series_categories"
        session = requests.Session()

        data = fetch_url(session, link)
        live_data = fetch_url(session, liveurl)
        vod_data = fetch_url(session, vodurl)
        series_data = fetch_url(session, seriesurl)

        live_categories = [category['category_name'] for category in live_data] if isinstance(live_data, list) else []
        vod_categories = [category['category_name'] for category in vod_data] if isinstance(vod_data, list) else []
        series_categories = [category['category_name'] for category in series_data] if isinstance(series_data, list) else []

        # Check if "telugu" or "telegu" is in live categories
        telugu_present = any("telugu" in category.lower() or "telegu" in category.lower() for category in live_categories)

        if isinstance(data, dict) and 'user_info' in data and 'username' in data['user_info']:
            status = data['user_info']['status']
            exp_date = data['user_info'].get('exp_date', "N/A")
            active_connections = data['user_info'].get('active_cons', "N/A")
            max_connections = data['user_info'].get('max_connections', "N/A")
            if exp_date != "N/A":
                exp_date = time.strftime('%d.%m.%Y', time.localtime(int(exp_date)))
            if status == 'Active':
                return (f"Active [●]", usuario, senha, exp_date, active_connections, max_connections,
                        live_categories, vod_categories, series_categories, telugu_present, link_m3u)
            else:
                return (f"INACTIVE [●]", usuario, senha, exp_date,
                        live_categories, vod_categories, series_categories, telugu_present, link_m3u)
        else:
            return "INACTIVE", usuario, senha, None, None, None, live_categories, vod_categories, series_categories, telugu_present, link_m3u
    except Exception as e:
        return f"Error: {str(e)}", None, None, None, None, None, None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        m3u_link = request.form['m3u_link']
        result = verificar_status_m3u(m3u_link)
    return render_template('index.html', result=result)

if __name__ == "__main__":
    app.run()
