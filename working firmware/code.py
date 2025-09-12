"""
Raspberry Pi Pico W NFC F19 Key Sender
======================================

Hardware Setup:
- Raspberry Pi Pico W
- SSD1306 OLED Display (128x32 or 128x64) 
- PN532 NFC Module (I2C mode)

Wiring (I2C):
- GP4 (SDA) -> OLED SDA + PN532 SDA
- GP5 (SCL) -> OLED SCL + PN532 SCL
- 3V3 -> OLED VCC + PN532 VCC
- GND -> OLED GND + PN532 GND

Required Libraries (copy to /lib folder):
- adafruit_ssd1306.mpy
- adafruit_pn532/ (entire folder)
- adafruit_bus_device/ (entire folder)
- adafruit_hid/ (entire folder)

Setup Instructions:
1. Install CircuitPython on Pico W
2. Copy required libraries to /lib folder
3. Copy this file as code.py to Pico W root
4. Scan any NFC tag to send F19 keypress and show display message

Function:
- Scans NFC tags and sends F19 keypress to host computer
- Displays visual patterns on OLED when tags are detected
- No WiFi or internet connection required

Download libraries from: https://circuitpython.org/libraries
"""

import board
import busio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_pn532.i2c import PN532_I2C

# New display stack imports (displayio based)
import displayio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_displayio_ssd1306 import SSD1306

# Release any previous displays (important after soft reloads)
displayio.release_displays()

# Globals for display objects
oled = None  # Will hold the display object
display_group = None
text_label = None
_loaded_font = None

# ---------------------------------------------------------------------------
# Display helper functions
# ---------------------------------------------------------------------------

def _load_font():
    global _loaded_font
    if _loaded_font:
        return _loaded_font
    # Try a list of candidate fonts (user can add any of these under /fonts)
    font_candidates = [
        "/fonts/Helvetica-Bold-16.bdf",
        "/fonts/helvR12.bdf",
        "/fonts/Arial-12.bdf",
        "/fonts/5x8.bdf",
    ]
    for path in font_candidates:
        try:
            _loaded_font = bitmap_font.load_font(path)
            print(f"Loaded font: {path}")
            return _loaded_font
        except Exception as e:
            pass
    # Fallback to built-in terminal font
    try:
        import terminalio
        _loaded_font = terminalio.FONT
        print("Using terminalio.FONT fallback")
    except Exception as e:
        _loaded_font = None
        print("No font available")
    return _loaded_font


def _ensure_label():
    global text_label, display_group, oled
    if oled is None:
        return False
    if text_label is None:
        fnt = _load_font()
        if fnt is None:
            return False
        display_group = displayio.Group()
        # Use anchor_point for true centering
        text_label = label.Label(fnt, text="", color=0xFFFFFF, anchor_point=(0.5, 0.5))
        text_label.anchored_position = (oled.width // 2, oled.height // 2)
        display_group.append(text_label)
        try:
            oled.show(display_group)
        except Exception as e:
            print(f"Display show error: {e}")
            return False
    return True


def _set_centered_text(txt):
    if not _ensure_label():
        return
    text_label.text = txt
    # Reapply anchored position after text change (height may change)
    text_label.anchored_position = (oled.width // 2, oled.height // 2)


def display_message(message):
    """Display a readable text message using displayio + bitmap font."""
    print(message)  # Removed 'Display:' prefix
    if oled is None:
        print("(OLED not available)")
        return
    try:
        if not _ensure_label():
            return
        msg = message.strip()
        # Special formatting
        if "Song Playing" in msg or msg.upper() == "SONG PLAYING":
            _set_centered_text("SONG\nPLAYING")
        elif msg.upper().startswith("NFC:"):
            uid_part = msg.split(":", 1)[-1].strip().replace(" ", "")
            if len(uid_part) > 8:
                uid_part = uid_part[:8]
            _set_centered_text("NFC\n" + uid_part)
        elif "READY" in msg.upper():
            _set_centered_text("NFC READY")
        elif "KEY FAILED" in msg.upper():
            _set_centered_text("KEY FAILED")
        elif "KEY" in msg.upper() or "F19" in msg.upper():
            _set_centered_text("F19")
        else:
            up = msg.upper()
            if len(up) <= 14:
                _set_centered_text(up)
            else:
                first = up[:14]
                second = up[14:28]
                _set_centered_text(first + "\n" + second)
    except Exception as e:
        print(f"Display error: {e}")

# ---------------------------------------------------------------------------
# Keyboard (unchanged)
# ---------------------------------------------------------------------------

def send_f19_key():
    """Send F19 key press when NFC tag is scanned"""
    if keyboard is not None:
        try:
            print("Sending F19 key press...")
            keyboard.press(Keycode.F19)
            keyboard.release(Keycode.F19)
            print("F19 key sent successfully!")
            return True
        except Exception as e:
            print(f"Failed to send F19 key: {e}")
            return False
    else:
        print("Keyboard not available - cannot send F19")
        return False

# ---------------------------------------------------------------------------
# I2C setup
# ---------------------------------------------------------------------------
print("Setting up I2C on GP4 (SDA) and GP5 (SCL)...")
try:
    print("Creating I2C bus...")
    i2c = busio.I2C(board.GP5, board.GP4, frequency=100000)
    print("I2C initialized successfully")
except Exception as e:
    print(f"I2C initialization failed: {e}")
    print("Continuing without I2C devices...")
    i2c = None

if i2c:
    try:
        print("Scanning I2C bus...")
        while not i2c.try_lock():
            pass
        devices = i2c.scan()
        i2c.unlock()
        print(f"Found I2C devices: {[hex(d) for d in devices]}")
    except Exception as e:
        print(f"I2C scan error: {e}")

# ---------------------------------------------------------------------------
# Keyboard init
# ---------------------------------------------------------------------------
print("Initializing USB HID keyboard...")
try:
    keyboard = Keyboard(usb_hid.devices)
    print("Keyboard initialized - ready to send F19 key presses")
except Exception as e:
    print(f"Keyboard initialization failed: {e}")
    print("Continuing without keyboard...")
    keyboard = None

# ---------------------------------------------------------------------------
# DisplayIO SSD1306 init
# ---------------------------------------------------------------------------
print("Setting up OLED display (displayio)...")
if i2c:
    try:
        # Address commonly 0x3C; adjust if needed
        display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
        oled = SSD1306(display_bus, width=128, height=32)
        print("DisplayIO SSD1306 initialized")
        display_message("NFC Ready")
    except Exception as e:
        print(f"Display init failed: {e}")
        oled = None
else:
    print("No I2C bus - running without OLED")

# ---------------------------------------------------------------------------
# PN532 NFC init
# ---------------------------------------------------------------------------
print("Setting up NFC module...")
pn532 = None
if i2c:
    try:
        pn532 = PN532_I2C(i2c, debug=False)
        ic, ver, rev, support = pn532.firmware_version
        print("Found PN532 firmware {}.{}".format(ver, rev))
        pn532.SAM_configuration()
        print("NFC module initialized successfully")
    except Exception as e:
        print(f"NFC initialization failed: {e}")
        pn532 = None
else:
    print("No I2C bus - running without NFC")

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
last_uid = None
print("Ready! Scan any NFC tag to send F19 keypress...")
print("Press Ctrl+C to stop")

try:
    while True:
        if pn532:
            try:
                uid = pn532.read_passive_target(timeout=0.5)
                if uid:
                    uid_str = "".join("{:02X}".format(i) for i in uid)
                    if uid_str != last_uid:
                        print(f"NFC Card detected! UID: {uid_str}")
                        display_message(f"NFC: {uid_str}")
                        if send_f19_key():
                            display_message("Playing heart playlist")
                        else:
                            display_message("Key Failed")
                        last_uid = uid_str
                        time.sleep(1.5)
                else:
                    if last_uid:
                        time.sleep(2)
                        last_uid = None
                        display_message("NFC Ready")
            except Exception as e:
                print(f"NFC scan error: {e}")
                time.sleep(1)
        else:
            print("NFC module not available - retrying in 5 seconds...")
            time.sleep(5)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram stopped by user")
except Exception as e:
    print(f"Unexpected error in main loop: {e}")
    print("Program terminated")

print("Code finished")
