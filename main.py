import os
import base64
import requests
import urllib3
from operator import itemgetter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIG ---
REGION = "na"
GLZ_URL = "https://glz-na-1.na.a.pvp.net"
PD_URL  = "https://pd.na.a.pvp.net"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

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
        session = requests.get(f"{local_url}/chat/v1/session", headers=headers, verify=False).json()
        version = session.get('client_version', "release-10.00-shipping-12345")

        return {
            'Authorization': f"Bearer {entitlements['accessToken']}",
            'X-Riot-Entitlements-JWT': entitlements['token'],
            'X-Riot-ClientVersion': version,
            'X-Riot-ClientPlatform': 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9'
        }
    except: return None

def get_rank_data(puuid, headers):
    try:
        url = f"{PD_URL}/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=10&queue=competitive"
        history = requests.get(url, headers=headers, json=True)
        if history.status_code == 200:
            matches = history.json().get('Matches', [])
            for match in matches:
                tier = match['TierAfterUpdate']
                if tier > 0:
                    return (tier, RANK_NAMES.get(tier, "Unranked"))
    except: pass
    return (0, "Unranked")

def print_team_table(team_name, players, color):
    sorted_players = sorted(players, key=lambda x: x['rank_data'][0], reverse=True)
    
    print(f"\n{color}=== {team_name} ({len(players)}) ==={RESET}")
    print(f"{'RANK':<12} | {'LVL':<4} | {'PLAYER ID'}")
    print("-" * 40)
    
    for p in sorted_players:
        rank_num, rank_name = p['rank_data']
        level = p['level']
        pid = p['Subject']
        
        warn = ""
        # Smurf Logic: Level < 40 and Rank > Silver 3
        if 0 < level < 40 and rank_num > 11:
            warn = f"{YELLOW}⚠️{color}"

        print(f"{color}{rank_name:<12} | {level:<4}{warn} | {pid[:8]}...{RESET}")

def main():
    print("--- 🕵️ ZERO TRACKER (OPTIMIZED) ---")
    path = os.path.join(os.getenv('LOCALAPPDATA'), r'Riot Games\Riot Client\Config\lockfile')
    if not os.path.exists(path): print("❌ Start Valorant!"); return
    
    with open(path, 'r') as f: data = f.read().split(':')
    lockfile = {'port': data[2], 'password': data[3]}
    
    headers = get_headers(lockfile)
    if not headers: return
    
    local_auth = base64.b64encode(f"riot:{lockfile['password']}".encode()).decode()
    me_req = requests.get(f"https://127.0.0.1:{lockfile['port']}/chat/v1/session", headers={'Authorization': f'Basic {local_auth}'}, verify=False).json()
    me = me_req['puuid']
    
    allies = []
    enemies = []
    my_team_id = None

    try:
        # Pre-Game
        pregame = requests.get(f"{GLZ_URL}/pregame/v1/players/{me}", headers=headers, json=True)
        if pregame.status_code == 200:
            print(f"{GREEN}🎯 AGENT SELECT FOUND!{RESET}")
            match_id = pregame.json()['MatchID']
            data = requests.get(f"{GLZ_URL}/pregame/v1/matches/{match_id}", headers=headers, json=True).json()
            raw_players = data['Teams'][0]['Players']
            
            for p in raw_players:
                # FIX: Read Level from Identity directly!
                lvl = p.get('PlayerIdentity', {}).get('AccountLevel', 0)
                
                allies.append({
                    'Subject': p['Subject'],
                    'rank_data': get_rank_data(p['Subject'], headers),
                    'level': lvl
                })

        # Live Game
        else:
            core = requests.get(f"{GLZ_URL}/core-game/v1/players/{me}", headers=headers, json=True)
            if core.status_code == 200:
                print(f"{RED}⚔️  LIVE MATCH FOUND!{RESET}")
                match_id = core.json()['MatchID']
                data = requests.get(f"{GLZ_URL}/core-game/v1/matches/{match_id}", headers=headers, json=True).json()
                raw_players = data['Players']
                
                for p in raw_players:
                    if p['Subject'] == me: my_team_id = p['TeamID']; break
                
                for p in raw_players:
                    # FIX: Read Level from Identity directly!
                    lvl = p.get('PlayerIdentity', {}).get('AccountLevel', 0)
                    
                    p_data = {
                        'Subject': p['Subject'],
                        'rank_data': get_rank_data(p['Subject'], headers),
                        'level': lvl
                    }
                    
                    if p['TeamID'] == my_team_id: allies.append(p_data)
                    else: enemies.append(p_data)
            else:
                print("💤 In Menu")
    except Exception as e:
        print(f"❌ Error: {e}")

    if allies: print_team_table("MY TEAM", allies, GREEN)
    if enemies: print_team_table("ENEMY TEAM", enemies, RED)

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"CRITICAL: {e}")
    input("\nPress Enter to close...")