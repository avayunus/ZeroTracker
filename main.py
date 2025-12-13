import os
import base64
import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION (NA FORCED) ---
REGION = "na"
GLZ_URL = "https://glz-na-1.na.a.pvp.net"
PD_URL  = "https://pd.na.a.pvp.net"

RANK_NAMES = {
    0: "Unranked", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3",
    6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3",
    9: "Silver 1", 10: "Silver 2", 11: "Silver 3",
    12: "Gold 1", 13: "Gold 2", 14: "Gold 3",
    15: "Plat 1", 16: "Plat 2", 17: "Plat 3",
    18: "Dia 1", 19: "Dia 2", 20: "Dia 3",
    21: "Asc 1", 22: "Asc 2", 23: "Asc 3",
    24: "Immo 1", 25: "Immo 2", 26: "Immo 3", 27: "Radiant"
}

def get_headers(lockfile):
    local_url = f"https://127.0.0.1:{lockfile['port']}"
    auth = base64.b64encode(f"riot:{lockfile['password']}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}

    try:
        entitlements = requests.get(f"{local_url}/entitlements/v1/token", headers=headers, verify=False).json()
        
        # Auto-detect Client Version
        version = "release-10.00-shipping-12345" 
        logs = os.path.join(os.getenv('LOCALAPPDATA'), r'VALORANT\Saved\Logs\ShooterGame.log')
        if os.path.exists(logs):
            with open(logs, 'r', errors='ignore') as f:
                match = re.search(r'CI server version: (.+)', f.read())
                if match: version = match.group(1).strip()

        return {
            'Authorization': f"Bearer {entitlements['accessToken']}",
            'X-Riot-Entitlements-JWT': entitlements['token'],
            'X-Riot-ClientVersion': version,
            'X-Riot-ClientPlatform': 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9'
        }
    except: return None

def get_rank(puuid, headers):
    try:
        mmr = requests.get(f"{PD_URL}/mmr/v1/players/{puuid}", headers=headers, json=True)
        if mmr.status_code == 200:
            skills = mmr.json()['QueueSkills']['competitive']['SeasonalInfoBySeasonID']
            latest_season = list(skills.keys())[-1]
            tier = skills[latest_season]['CompetitiveTier']
            return RANK_NAMES.get(tier, "Unknown")
    except: pass
    return "Unknown"

def main():
    print("--- 🕵️ ZERO TRACKER (LIVE) ---")
    path = os.path.join(os.getenv('LOCALAPPDATA'), r'Riot Games\Riot Client\Config\lockfile')
    if not os.path.exists(path): print("❌ Start Valorant!"); return
    
    with open(path, 'r') as f: data = f.read().split(':')
    lockfile = {'port': data[2], 'password': data[3]}
    
    headers = get_headers(lockfile)
    if not headers: return
    
    # Get My PUUID
    local_auth = base64.b64encode(f"riot:{lockfile['password']}".encode()).decode()
    me = requests.get(f"https://127.0.0.1:{lockfile['port']}/chat/v1/session", headers={'Authorization': f'Basic {local_auth}'}, verify=False).json()['puuid']

    print(f"✅ Connected to NA Server")
    
    # 1. CHECK PRE-GAME (Agent Select)
    pregame = requests.get(f"{GLZ_URL}/pregame/v1/players/{me}", headers=headers, json=True)
    if pregame.status_code == 200:
        print("🎯 AGENT SELECT FOUND!")
        match_id = pregame.json()['MatchID']
        data = requests.get(f"{GLZ_URL}/pregame/v1/matches/{match_id}", headers=headers, json=True).json()
        players = data['Teams'][0]['Players']
        
        print(f"\n{'RANK':<12} | {'PLAYER ID'}")
        print("-" * 35)
        for p in players:
            print(f"{get_rank(p['Subject'], headers):<12} | {p['Subject'][:8]}...")

    # 2. CHECK CORE-GAME (Live Match)
    else:
        core = requests.get(f"{GLZ_URL}/core-game/v1/players/{me}", headers=headers, json=True)
        if core.status_code == 200:
            print("⚔️  LIVE MATCH FOUND!")
            match_id = core.json()['MatchID']
            data = requests.get(f"{GLZ_URL}/core-game/v1/matches/{match_id}", headers=headers, json=True).json()
            players = data['Players'] # Note: Live game structure is slightly different
            
            print(f"\n{'RANK':<12} | {'PLAYER ID'}")
            print("-" * 35)
            for p in players:
                print(f"{get_rank(p['Subject'], headers):<12} | {p['Subject'][:8]}...")
        else:
            print("💤 In Menu")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    
    # This line forces the window to stay open
    input("\nPress Enter to close...")