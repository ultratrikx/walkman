import network
import urequests
import json
import time
import machine
from machine import Pin, SPI, I2C
from ssd1306 import SSD1306_I2C
from mfrc522 import MFRC522

WIFI_SSID = "WIFI_SSID"
WIFI_PASSWORD = "WIFI_PASSWORD"

HA_ADDRESS = "http://HOME_ASSISTANT_IP:8123"
HA_TOKEN = "TOKEN"
MEDIA_PLAYER_ENTITY = "media_player.living_room_speaker"

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32
OLED_I2C_ADDR = 0x3C

MUSIC_MAPPINGS = [
    {"tag_id": 123456789, "name": "Jazz Playlist", "url": "https://open.spotify.com/playlist/YOUR_JAZZ_PLAYLIST"},
    {"tag_id": 987654321, "name": "Rock Classics", "url": "https://open.spotify.com/playlist/YOUR_ROCK_PLAYLIST"},
    {"tag_id": 456789123, "name": "Classical Symphony", "url": "https://open.spotify.com/album/YOUR_CLASSICAL_ALBUM"},
    {"tag_id": 789123456, "name": "Podcasts", "url": "https://open.spotify.com/show/YOUR_PODCAST"},
    {"tag_id": 234567891, "name": "Radio Station", "url": "https://tunein.com/radio/YOUR_STATION"}
]

current_song_name = "No song playing"
current_artist = ""
is_playing = False
last_tag_id = 0
last_tag_read_time = 0
tag_presence_timeout = 5000
tag_processed = False
last_status_check_time = 0
status_check_interval = 10000

led = Pin("LED", Pin.OUT)

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
display = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c, addr=OLED_I2C_ADDR)

spi = SPI(1, baudrate=1000000, polarity=0, phase=0)
cs = Pin(5, Pin.OUT)
reset = Pin(22, Pin.OUT)
rfid = MFRC522(spi, cs, reset)

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"Connecting to WiFi {WIFI_SSID}")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    max_attempts = 20
    attempts = 0
    
    while not wlan.isconnected() and attempts < max_attempts:
        led.toggle()
        time.sleep(0.5)
        attempts += 1
        print(".", end="")
    
    if wlan.isconnected():
        print(f"\nConnected! IP: {wlan.ifconfig()[0]}")
        led.value(1)
        return True
    else:
        print("\nFailed to connect. Will retry later.")
        led.value(0)
        return False

def update_display(title, subtitle, playing):
    display.fill(0)
    
    if playing:
        display.text("Now Playing:", 0, 0, 1)
    else:
        display.text("Ready:", 0, 0, 1)
    
    if len(title) > 21:
        title = title[:18] + "..."
    display.text(title, 0, 10, 1)
    
    if len(subtitle) > 21:
        subtitle = subtitle[:18] + "..."
    display.text(subtitle, 0, 20, 1)
    
    display.show()

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

def play_music_for_tag(tag_id):
    global current_song_name, is_playing
    
    for mapping in MUSIC_MAPPINGS:
        if mapping["tag_id"] == tag_id:
            print(f"Found matching music: {mapping['name']}")
            
            current_song_name = mapping["name"]
            
            update_display(current_song_name, "Loading...", True)
            
            success = call_home_assistant_to_play_music(mapping["url"])
            
            if success:
                is_playing = True
                update_display(current_song_name, "Playing", True)
            else:
                update_display(current_song_name, "Failed to play", False)
            
            return success
    
    update_display("Unknown Tag", f"ID: {tag_id}", False)
    return False

def call_home_assistant_to_play_music(media_url):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi not connected")
        return False
    
    api_url = f"{HA_ADDRESS}/api/services/media_player/play_media"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HA_TOKEN}"
    }
    
    payload = {
        "entity_id": MEDIA_PLAYER_ENTITY,
        "media_content_id": media_url,
        "media_content_type": "music"
    }
    
    try:
        response = urequests.post(api_url, headers=headers, json=payload)
        
        success = response.status_code == 200 or response.status_code == 201
        print(f"HTTP Response code: {response.status_code}")
        
        response_text = response.text
        response.close()
        
        print(response_text)
        return success
    
    except Exception as e:
        print(f"Error sending request: {e}")
        return False

def check_media_player_status():
    global current_song_name, current_artist, is_playing
    
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        return
    
    api_url = f"{HA_ADDRESS}/api/states/{MEDIA_PLAYER_ENTITY}"
    
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}"
    }
    
    try:
        response = urequests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = json.loads(response.text)
            response.close()
            
            state = data.get("state", "")
            is_playing = (state == "playing")
            
            attributes = data.get("attributes", {})
            if "media_title" in attributes:
                current_song_name = attributes["media_title"]
                
                if "media_artist" in attributes:
                    current_artist = attributes["media_artist"]
                else:
                    current_artist = ""
                
                update_display(current_song_name, current_artist, is_playing)
        else:
            print(f"Error getting player state: {response.status_code}")
            response.close()
    
    except Exception as e:
        print(f"Error checking media player status: {e}")

def main():
    global last_tag_id, tag_processed, last_tag_read_time, last_status_check_time
    
    update_display("Walkman", "Starting...", False)
    
    if not connect_to_wifi():
        pass
    
    while True:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            print("WiFi connection lost. Reconnecting...")
            connect_to_wifi()
        
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_status_check_time) > status_check_interval:
            check_media_player_status()
            last_status_check_time = current_time
        
        tag_id = get_tag_id()
        
        if tag_id is not None:
            print(f"Tag detected! ID: {tag_id}")
            
            if (tag_id != last_tag_id or 
                (time.ticks_diff(current_time, last_tag_read_time) > tag_presence_timeout and not tag_processed)):
                last_tag_id = tag_id
                tag_processed = True
                
                if play_music_for_tag(tag_id):
                    print("Music request sent to Home Assistant")
                else:
                    print("Unknown tag or error sending request")
            
            last_tag_read_time = current_time
        
        elif time.ticks_diff(current_time, last_tag_read_time) > tag_presence_timeout:
            tag_processed = False
        
        time.sleep(0.1)

if __name__ == "__main__":
    main()