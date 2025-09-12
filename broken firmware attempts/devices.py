import requests

# Paste your temporary access token here
ACCESS_TOKEN = "BQDwMkYss6toGDqkR_t5JjhLyfeZKkOhCj-lik8wxWiKcvGwowqN9TolXgQbgzW36DHVLJpO90La9-1ynBHSN2JdU-weTxV_IaQU9Q7iWYNJY-2qRe_Pkls88s4GCDSqqnWN543uc0U"

url = "https://api.spotify.com/v1/me/player/devices"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    devices = resp.json().get("devices", [])
    if not devices:
        print("No active devices found. Make sure Spotify is open on a device.")
    for d in devices:
        print("Name:", d["name"])
        print("Type:", d["type"])
        print("ID:", d["id"])
        print("Is Active:", d["is_active"])
        print("---")
else:
    print("Error:", resp.status_code, resp.text)
