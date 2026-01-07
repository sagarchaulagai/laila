import os
import glob
import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw
import time
import threading

# Configuration
if getattr(sys, 'frozen', False):
    # If run as bundled EXE, PyInstaller unpacks data to sys._MEIPASS
    BASE_DIR = sys._MEIPASS
else:
    # If run as script, use the script's directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global state for sequential detection
state = {
    'status': 'IDLE',   # IDLE, WAIT_DIGIT, WAIT_CHAR
    'digit': None,
    'last_time': 0,
    'mapping': {}       # {'1a': 'path/to/1a.txt'}
}

TIMEOUT = 3.0  # Seconds to wait between keystrokes in sequential mode

def create_tray_icon():
    image_path = os.path.join(BASE_DIR, 'logo.png')
    if os.path.exists(image_path):
        return Image.open(image_path)
    
    # Fallback default
    width = 64
    height = 64
    color_bg = "black"
    color_fg = "white"
    
    image = Image.new('RGB', (width, height), color_bg)
    dc = ImageDraw.Draw(image)
    
    dc.rectangle((16, 16, 48, 48), outline=color_fg, width=3)
    dc.text((24, 20), "Copy", fill=color_fg)
    
    return image

def copy_file_content(filepath):
    """Reads the file and copies its content to clipboard."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        pyperclip.copy(content)
        print(f"Copied content from {os.path.basename(filepath)}")
    except Exception as e:
        print(f"Failed to copy {filepath}: {e}")

def load_files_mapping():
    """Scans directories and builds a mapping of key sequences to file paths."""
    mapping = {}
    print(f"Scanning {BASE_DIR} for files...")
    
    for item in os.listdir(BASE_DIR):
        dir_path = os.path.join(BASE_DIR, item)
        
        if os.path.isdir(dir_path) and item.isdigit():
            digit = item
            txt_files = glob.glob(os.path.join(dir_path, "*.txt"))
            
            for filepath in txt_files:
                filename = os.path.basename(filepath)
                name, ext = os.path.splitext(filename)
                
                # Check if file starts with the digit (e.g. 1a.txt in folder 1)
                if name.startswith(digit):
                    char_part = name[len(digit):]
                    if char_part:
                        # Key is digit + char (e.g. "1a")
                        key = f"{digit}{char_part.lower()}"
                        mapping[key] = filepath
    return mapping

def on_ctrl_c():
    """Triggered when Ctrl+C is pressed."""
    # We always reset state to WAIT_DIGIT on Ctrl+C
    state['status'] = 'WAIT_DIGIT'
    state['last_time'] = time.time()
    state['digit'] = None
    print("Ctrl+C detected. Waiting for digit...")

def on_key_event(event):
    """Global key hook to handle the sequential state machine."""
    # Only process key down events
    if event.event_type != 'down':
        return

    # Check timeout
    if state['status'] != 'IDLE' and (time.time() - state['last_time'] > TIMEOUT):
        print("Timeout. Resetting sequence.")
        state['status'] = 'IDLE'
        state['digit'] = None

    # State Machine
    if state['status'] == 'WAIT_DIGIT':
        # Ignore Ctrl or C if they are being held or repeated immediately
        if event.name in ['ctrl', 'right ctrl', 'left ctrl', 'c']:
            return
            
        if event.name.isdigit():
            state['digit'] = event.name
            state['status'] = 'WAIT_CHAR'
            state['last_time'] = time.time()
            print(f"Digit '{state['digit']}' received. Waiting for char...")
        else:
            # If user presses something else, reset (unless it's a modifier we want to ignore)
            # Here we reset on any non-digit input to avoid confusion
            print(f"Invalid input '{event.name}'. Resetting.")
            state['status'] = 'IDLE'

    elif state['status'] == 'WAIT_CHAR':
        if event.name in ['ctrl', 'right ctrl', 'left ctrl']:
            return

        # We allow any character that forms a valid key in our mapping
        # But usually these are letters.
        if len(event.name) == 1:
            potential_key = f"{state['digit']}{event.name.lower()}"
            
            if potential_key in state['mapping']:
                print(f"Sequence complete: {potential_key}")
                copy_file_content(state['mapping'][potential_key])
            else:
                print(f"No match for sequence: {potential_key}")
            
            # Reset after attempt
            state['status'] = 'IDLE'
            state['digit'] = None
        else:
             print(f"Invalid char '{event.name}'. Resetting.")
             state['status'] = 'IDLE'

def register_hotkeys():
    state['mapping'] = load_files_mapping()
    
    # 1. Register Simultaneous Hotkeys: Ctrl+C+Digit+Char
    # Note: keyboard module order is modifiers+keys. 
    # 'ctrl+c+1+a' means Ctrl and C and 1 and A are all held.
    
    for key, filepath in state['mapping'].items():
        # key is like '1a'. We want 'ctrl+c+1+a'
        digit = key[0]
        char_part = key[1:]
        
        simultaneous_hotkey = f"ctrl+c+{digit}+{char_part}"
        try:
            keyboard.add_hotkey(simultaneous_hotkey, lambda path=filepath: copy_file_content(path))
            print(f"Registered simultaneous: {simultaneous_hotkey} -> {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Failed to register {simultaneous_hotkey}: {e}")

    # 2. Register Sequential Trigger: Ctrl+C
    # We use add_hotkey for 'ctrl+c'. 
    # suppress=False ensures generic copy still works (and passes through to us).
    try:
        keyboard.add_hotkey('ctrl+c', on_ctrl_c, suppress=False)
        print("Registered sequential trigger: ctrl+c")
    except Exception as e:
        print(f"Failed to register trigger: {e}")

    # 3. Hook all keys for the state machine
    keyboard.hook(on_key_event)

def quit_app(icon, item):
    icon.stop()
    os._exit(0)

def main():
    register_hotkeys()
    
    icon = pystray.Icon(
        "ClipboardManager",
        create_tray_icon(),
        menu=pystray.Menu(
            pystray.MenuItem("Quit", quit_app)
        )
    )
    
    print("Application started. Check system tray.")
    print("Modes available:")
    print("1. Simultaneous: Hold Ctrl + C + <Digit> + <Char>")
    print("2. Sequential: Press Ctrl+C (release), then <Digit>, then <Char>")
    
    icon.run()

if __name__ == "__main__":
    main()
