import os
import base64
import json
import urllib3
import requests

# Disable SSL warnings (Riot uses a self-signed cert, which is normal for local APIs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_lockfile_data():
    # This is the standard path where Riot dumps the connection info
    path = os.path.join(os.getenv('LOCALAPPDATA'), r'Riot Games\Riot Client\Config\lockfile')
    
    if not os.path.exists(path):
        print("❌ Lockfile not found. Is Valorant/Riot Client running?")
        return None
    
    # The lockfile contains: ProcessName:PID:Port:Password:Protocol
    with open(path, 'r') as f:
        data = f.read().split(':')
        
    return {
        'port': data[2],
        'password': data[3],
        'base_url': f"https://127.0.0.1:{data[2]}"
    }

def check_connection():
    data = get_lockfile_data()
    if not data:
        return

    # To talk to the API, we need a "Basic Auth" header
    # Username is always 'riot', password is the one from the file
    auth_str = f"riot:{data['password']}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'X-Riot-ClientPlatform': 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9'
    }

    try:
        # TEST REQUEST: Ask the client "Who is logged in?"
        response = requests.get(f"{data['base_url']}/chat/v4/friends", headers=headers, verify=False)
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Connected to Local API on Port {data['port']}")
            print(f"✅ Found {len(response.json())} friends online.")
        else:
            print(f"⚠️ Connected, but got error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_connection()