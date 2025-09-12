import network
import urequests
import json
import time
from machine import Pin, I2C, SPI
from ssd1306 import SSD1306_I2C
from mfrc522 import MFRC522

# ---------------- CONFIG ----------------
WIFI_SSID = "NightingaleTP"
WIFI_PASSWORD = "Vernonflower999"

# Spotify API credentials
SPOTIFY_CLIENT_ID = "2d5d8cc0d20d4f5381a5398bef6b6ddc"
SPOTIFY_CLIENT_SECRET = "af8d16027c3e49d3a4adc879a6cde04f"
SPOTIFY_REFRESH_TOKEN = "AQBxrQVigYlHMHUlCKYXu5BuU8hbuvHbj42KziaM-H3NUFv8g0iyTqwRgSpTNKFAn4TMk0W-0xV5ILwAsA8-8kWS9GtY2_arlB_DWSaMfG1d_O4uMZ9DiccznWD9wiREc5A"
SPOTIFY_DEVICE_ID = "794a06f9d0ff19ba4adb06129b4f34340b724843"          # the speaker/device you want to play on

# RFID mappings (tag_id -> Spotify URI)
MUSIC_MAPPINGS = [
    {"tag_id": 123456789, "name": "Jazz Playlist", "uri": "spotify:playlist:0FZAiQwdQD7p7PsiManlTa"},
    {"tag_id": 987654321, "name": "Rock Classics", "uri": "spotify:playlist:YOUR_ROCK_PLAYLIST_ID"},
]


# ---------------- HARDWARE SETUP ----------------
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32
OLED_I2C_ADDR = 0x3C

led = Pin("LED", Pin.OUT)
# OLED on GP0 (SDA), GP1 (SCL)
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
display = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c, addr=OLED_I2C_ADDR)

# RN532 NFC Reader wiring:
#   SCK  -> GP6
#   MISO -> GP4
#   MOSI -> GP7
#   SS   -> GP5
#   RST  -> GP22
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
cs = Pin(5, Pin.OUT)
reset = Pin(22, Pin.OUT)
rfid = MFRC522(spi, cs, reset)

access_token = None
access_token_expiry = 0

# ---------------- WIFI ----------------
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    attempts = 0
    while not wlan.isconnected() and attempts < 20:
        time.sleep(0.5)
        led.toggle()
        attempts += 1
    led.value(1 if wlan.isconnected() else 0)
    return wlan.isconnected()

# ---------------- DISPLAY ----------------
def update_display(title, subtitle):
    display.fill(0)
    display.text(title[:21], 0, 0, 1)
    display.text(subtitle[:21], 0, 12, 1)
    display.show()

# ---------------- SPOTIFY AUTH ----------------
def refresh_access_token():
    global access_token, access_token_expiry

    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = "grant_type=refresh_token&refresh_token={}&client_id={}&client_secret={}".format(
        SPOTIFY_REFRESH_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    try:
        res = urequests.post(url, data=body, headers=headers)
        if res.status_code == 200:
            data = res.json()
            access_token = data["access_token"]
            access_token_expiry = time.time() + data.get("expires_in", 3600)
            print("[+] Got new access token")
            return True
        else:
            print("[-] Failed to refresh token", res.text)
        res.close()
    except Exception as e:
        print("Auth error:", e)
    return False

# ---------------- SPOTIFY CONTROL ----------------
def spotify_play(uri):
    if not access_token or time.time() > access_token_expiry:
        refresh_access_token()

    url = "https://api.spotify.com/v1/me/player/play?device_id={}".format(SPOTIFY_DEVICE_ID)
    headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
    body = json.dumps({"uris": [uri]})

    try:
        res = urequests.put(url, data=body, headers=headers)
        print("Play status:", res.status_code)
        res.close()
        return res.status_code in (200, 204)
    except Exception as e:
        print("Error playing:", e)
        return False

def spotify_current():
    if not access_token or time.time() > access_token_expiry:
        refresh_access_token()
    try:
        res = urequests.get("https://api.spotify.com/v1/me/player/currently-playing", headers={"Authorization": "Bearer " + access_token})
        if res.status_code == 200:
            data = res.json()
            name = data["item"]["name"]
            artist = ", ".join([a["name"] for a in data["item"]["artists"]])
            update_display(name, artist)
        res.close()
    except Exception as e:
        print("Error fetching track:", e)

# ---------------- RFID ----------------
def get_tag_id():
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status != rfid.OK:
        return None
    (status, uid) = rfid.anticoll()
    if status != rfid.OK:
        return None
    id_number = 0
    for i in range(len(uid)):
        id_number = (id_number << 8) | uid[i]
    return id_number

# ---------------- MAIN ----------------
def main():
    connect_to_wifi()
    update_display("Spotify RFID", "Ready")

    last_tag = None
    while True:
        tag_id = get_tag_id()
        if tag_id and tag_id != last_tag:
            last_tag = tag_id
            found = next((m for m in MUSIC_MAPPINGS if m["tag_id"] == tag_id), None)
            if found:
                update_display("Loading...", found["name"])
                if spotify_play(found["uri"]):
                    update_display("Playing", found["name"])
                    time.sleep(2)
                    spotify_current()
                else:
                    update_display("Error", "Spotify fail")
            else:
                update_display("Unknown Tag", str(tag_id))
        time.sleep(0.5)

if __name__ == "__main__":
    main()
