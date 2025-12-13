import os
import base64
import json
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_lockfile_data():
    path = os.path.join(os.getenv('LOCALAPPDATA'), r'Riot Games\Riot Client\Config\lockfile')
    
    if not os.path.exists(path):
        print("❌ Lockfile not found. Is Valorant running?")
        return None
    
    with open(path, 'r') as f:
        data = f.read().split(':')
        
    return {
        'port': data[2],
        'password': data[3],
        'base_url': f"https://127.0.0.1:{data[2]}"
    }

def get_current_user():
    data = get_lockfile_data()
    if not data:
        return

    headers = {
        'Authorization': f"Basic {base64.b64encode(f'riot:{data['password']}'.encode()).decode()}"
    }

    try:
        # STEP 1: Get "My" Session (Name, Tag, PUUID)
        # This is the most critical step. It tells us WHO is playing.
        session = requests.get(f"{data['base_url']}/chat/v1/session", headers=headers, verify=False)
        
        if session.status_code == 200:
            user_info = session.json()
            name = user_info.get('game_name')
            tag = user_info.get('game_tag')
            puuid = user_info.get('puuid')
            
            print(f"✅ LOGGED IN AS: {name}#{tag}")
            print(f"🔑 PUUID: {puuid}")
            print("--------------------------------------------------")
            
            # STEP 2: Are we in a Pre-Game Lobby? (Agent Select)
            # We use the PUUID to check if a pre-game exists for us.
            pregame = requests.get(f"https://127.0.0.1:{data['port']}/pregame/v1/players/{puuid}", headers=headers, verify=False)
            
            if pregame.status_code == 200:
                print("🎯 STATUS: In Agent Select!")
                match_id = pregame.json().get('MatchID')
                print(f"🆔 Match ID: {match_id}")
            elif pregame.status_code == 404:
                print("💤 STATUS: In Menu (No active pre-game found)")
            else:
                print(f"⚠️ STATUS CHECK: {pregame.status_code}")
                
        else:
            print(f"❌ Failed to get session: {session.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_current_user()