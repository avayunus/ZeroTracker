import os
import base64
import requests
import urllib3
import urllib.parse
import webbrowser  # New import for opening links
import customtkinter as ctk
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIG (LOCAL ONLY) ---
REGION = "na" 
GLZ_URL = f"https://glz-{REGION}-1.{REGION}.a.pvp.net"
PD_URL  = f"https://pd.{REGION}.a.pvp.net"

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

def get_names(puuids, headers):
    try:
        url = f"{PD_URL}/name-service/v2/players"
        response = requests.put(url, headers=headers, json=puuids, verify=False)
        names = {}
        if response.status_code == 200:
            for player in response.json():
                names[player['Subject']] = f"{player['GameName']}#{player['TagLine']}"
        return names
    except: return {}

def get_rank_data(puuid, headers):
    try:
        url = f"{PD_URL}/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=10&queue=competitive"
        history = requests.get(url, headers=headers, json=True)
        if history.status_code == 200:
            matches = history.json().get('Matches', [])
            for match in matches:
                tier = match['TierAfterUpdate']
                if tier > 0: return (tier, RANK_NAMES.get(tier, "Unranked"))
    except: pass
    return (0, "Unranked")

# --- GUI CLASS ---
class ZeroTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ZeroTracker V12 - Tracker.gg Link") 
        self.geometry("1000x600") 
        self.minsize(900, 400)
        self.attributes("-topmost", True)
        ctk.set_appearance_mode("dark")
        
        # HeaderFrame
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        
        self.label = ctk.CTkLabel(self.header_frame, text="READY TO SCAN", font=("Arial", 16, "bold"))
        self.label.pack(side="left", padx=10)

        self.btn = ctk.CTkButton(self.header_frame, text="SCAN LOBBY", command=self.refresh_data, 
                                 fg_color="#FF4B50", width=120)
        self.btn.pack(side="right", padx=10)

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Frames
        self.my_team_frame = ctk.CTkScrollableFrame(self.main_container, label_text="MY TEAM (GREEN)")
        self.my_team_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5)) 
        
        self.enemy_team_frame = ctk.CTkScrollableFrame(self.main_container, label_text="ENEMY TEAM (RED)")
        self.enemy_team_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def refresh_data(self):
        self.btn.configure(state="disabled", text="SCANNING...") 
        threading.Thread(target=self.fetch_and_display).start()

    def fetch_and_display(self):
        # Clear UI
        for widget in self.my_team_frame.winfo_children(): widget.destroy()
        for widget in self.enemy_team_frame.winfo_children(): widget.destroy()

        path = os.path.join(os.getenv('LOCALAPPDATA'), r'Riot Games\Riot Client\Config\lockfile')
        if not os.path.exists(path):
            self.label.configure(text="VALORANT NOT FOUND")
            self.reset_btn()
            return

        try:
            with open(path, 'r') as f: data = f.read().split(':')
            lockfile = {'port': data[2], 'password': data[3]}
            headers = get_headers(lockfile)
            if not headers: 
                self.reset_btn()
                return

            local_auth = base64.b64encode(f"riot:{lockfile['password']}".encode()).decode()
            me_req = requests.get(f"https://127.0.0.1:{lockfile['port']}/chat/v1/session", headers={'Authorization': f'Basic {local_auth}'}, verify=False).json()
            me = me_req['puuid']

            players = []
            is_pregame = False
            
            pregame = requests.get(f"{GLZ_URL}/pregame/v1/players/{me}", headers=headers, json=True)
            if pregame.status_code == 200:
                is_pregame = True
                self.label.configure(text="AGENT SELECT")
                match_id = pregame.json()['MatchID']
                data = requests.get(f"{GLZ_URL}/pregame/v1/matches/{match_id}", headers=headers, json=True).json()
                players = data['Teams'][0]['Players']
            else:
                core = requests.get(f"{GLZ_URL}/core-game/v1/players/{me}", headers=headers, json=True)
                if core.status_code == 200:
                    self.label.configure(text="LIVE MATCH")
                    match_id = core.json()['MatchID']
                    data = requests.get(f"{GLZ_URL}/core-game/v1/matches/{match_id}", headers=headers, json=True).json()
                    players = data['Players']
                else:
                    self.label.configure(text="IDLE (IN MENU)")
                    self.reset_btn()
                    return

            puuids = [p['Subject'] for p in players]
            names_dict = get_names(puuids, headers)

            my_team = []
            enemy_team = []
            my_team_id = "Blue"

            if not is_pregame:
                for p in players:
                    if p['Subject'] == me: my_team_id = p['TeamID']

            for p in players:
                pid = p['Subject']
                lvl = p.get('PlayerIdentity', {}).get('AccountLevel', 0)
                rank_num, rank_name = get_rank_data(pid, headers)
                full_name = names_dict.get(pid, "Unknown#0000")
                
                is_smurf = False
                if 0 < lvl < 40 and rank_num > 11: is_smurf = True

                p_obj = {
                    "name": full_name, "rank_num": rank_num, 
                    "rank_name": rank_name, "level": lvl, "smurf": is_smurf
                }

                if is_pregame: my_team.append(p_obj)
                else:
                    if p['TeamID'] == my_team_id: my_team.append(p_obj)
                    else: enemy_team.append(p_obj)

            my_team.sort(key=lambda x: x['rank_num'], reverse=True)
            enemy_team.sort(key=lambda x: x['rank_num'], reverse=True)

            self.render_table(self.my_team_frame, my_team, "#00FF7F")
            self.render_table(self.enemy_team_frame, enemy_team, "#FF4B50")
            
        except Exception as e:
            print(f"Loop Error: {e}")
            self.label.configure(text="ERROR")

        self.reset_btn()

    def reset_btn(self):
        self.btn.configure(state="normal", text="SCAN LOBBY")

    def render_table(self, frame, team_data, color):
        for p in team_data:
            row = ctk.CTkFrame(frame, fg_color="#2B2B2B")
            row.pack(fill="x", pady=2)

            # Rank & Level
            ctk.CTkLabel(row, text=p['rank_name'], width=70, text_color=color, font=("Consolas", 12, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"Lvl {p['level']}", width=60, text_color="white", font=("Consolas", 12)).pack(side="left")

            # BUTTON: Tracker.gg Link (Right Side)
            # We create this first so it stays on the right
            def open_tracker(name_tag=p['name']):
                if "#" in name_tag:
                    # Format: Name#TAG -> Name%23TAG
                    safe_url = urllib.parse.quote(name_tag).replace('%23', '#') # Tracker uses # symbol sometimes but let's be safe
                    # Actually tracker URL format is: https://tracker.gg/valorant/profile/riot/Name%23TAG/overview
                    # We need to escape the # as %23
                    safe_url = urllib.parse.quote(name_tag)
                    url = f"https://tracker.gg/valorant/profile/riot/{safe_url}/overview"
                    webbrowser.open(url)

            # Tracker Button
            ctk.CTkButton(row, text="TRN", width=40, height=20, command=open_tracker, 
                          fg_color="#444", hover_color="#666").pack(side="right", padx=5)

            # Smurf Tag
            if p['smurf']:
                ctk.CTkLabel(row, text="⚠️", text_color="yellow", font=("Arial", 14)).pack(side="right", padx=5)

            # Name (Fills remaining space)
            ctk.CTkLabel(row, text=p['name'], anchor="w", font=("Arial", 12)).pack(side="left", padx=5, fill="x", expand=True)

if __name__ == "__main__":
    app = ZeroTrackerApp()
    app.mainloop()