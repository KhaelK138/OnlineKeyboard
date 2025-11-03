from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import pyautogui
import keyboard
import screen_brightness_control as sbc
import time
import os
import mss
import io
import argparse
from flask import Response
from PIL import Image, ImageDraw
from functools import wraps


app = Flask(__name__)
app.secret_key = os.urandom(12)

CONFIG_FILE = 'config.txt'

def get_password():
    return open(CONFIG_FILE).read().strip().split('=')[1]

def set_password(new_pass):
    with open(CONFIG_FILE, 'w') as f:
        f.write(f"app_pass={new_pass}\n")

def is_default_password(password):
    return get_password() == "changeme" and password == "changeme"

brightness = sbc.get_brightness()
pyautogui.FAILSAFE = False


# Dictionary to keep track of which keys are toggled (held down)
toggle_keys = {
    "Shift": False,
    "Control": False,
    "Alt": False
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'auth_token' not in session:
            return redirect(url_for('login'))  # Redirect to login if unauthenticated
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    return render_template('index.html', toggle_keys=toggle_keys)

# Login Functionality

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if not password:
            return render_template('login.html')
        # Force password change if default
        if is_default_password(password):
            return redirect(url_for('change_pass'))
        
        if password == get_password():
            session['auth_token'] = 'authenticated'  # Set a session token
            return redirect(url_for('home'))  # Redirect to the main page after login
        else:
            return render_template('login.html')  
    return render_template('login.html')  # Serve the login page template

@app.route('/change_pass', methods=['GET', 'POST'])
def change_pass():
    """
    Force password change if it's default, but require knowing the current password first.
    """
    if request.method == 'POST':
        current = request.form['current_password']
        new_pass = request.form['new_password']
        confirm_pass = request.form['confirm_password']
        if not current or not new_pass or not confirm_pass:
            return render_template('change_pass.html', error="All fields are required")

        # verify current password
        if current != get_password():
            return render_template('change_pass.html', error="Incorrect current password")

        # prevent reusing default
        if new_pass == "changeme":
            return render_template('change_pass.html', error="Password cannot be default password")

        # confirm match
        if new_pass != confirm_pass:
            return render_template('change_pass.html', error="Passwords do not match")

        set_password(new_pass)
        return redirect(url_for('login'))

    return render_template('change_pass.html')

# App Functionality

@app.route('/move_mouse', methods=['POST'])
@login_required
def move_mouse():
    data = request.json
    dx = data['dx']
    dy = data['dy']
    
    # Scale the movement (adjust these values as needed)
    scale_factor = 0.5
    dx_scaled = int(dx * scale_factor)
    dy_scaled = int(dy * scale_factor)
    
    # Move the mouse relative to its current position
    pyautogui.moveRel(dx_scaled, dy_scaled)
    
    return jsonify({"status": "success"})

def start_stream():
    @app.route('/stream')
    @login_required
    def stream():
        def generate():
            sct = mss.mss()
            while True:
                # Capture screen
                sct_img = sct.grab(sct.monitors[0])
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                # Get cursor position
                x, y = pyautogui.position()

                # Draw simple cursor overlay (red circle)
                draw = ImageDraw.Draw(img)
                r = 5
                draw.ellipse((x-r, y-r, x+r, y+r), fill="red", outline="black")

                # Encode to JPEG
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=50)
                frame = buf.getvalue()

                # Stream as MJPEG
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/features')
@login_required
def features():
    return jsonify({"streaming": args.stream})

@app.route('/click_mouse', methods=['POST'])
@login_required
def click_mouse():
    data = request.json
    action = data['action']
    
    if action == 'click':
        pyautogui.click()
    
    return jsonify({"status": "success"})

# Route to handle key press events
@app.route('/press_key', methods=['POST'])
@login_required
def press_key():
    key = request.form['key']

    if key == 'Off':
        keyboard.press_and_release('win+r')
        time.sleep(0.5)  # Wait for the Run dialog to appear
        keyboard.write('shutdown /h')
        keyboard.press_and_release('enter')
        return redirect(url_for('home'))

    # Handle toggleable keys (Shift, Control, Escape)
    if key in toggle_keys:
        if toggle_keys[key]:
            keyboard.release(key.lower())
            toggle_keys[key] = False
        else:
            keyboard.press(key.lower())
            toggle_keys[key] = True
    else:
        keyboard.press_and_release(key.lower())
    
    return redirect(url_for('home'))

@app.route('/get_toggle_states', methods=['GET'])
@login_required
def get_toggle_states():
    return jsonify(toggle_keys)

# Media Controls
@app.route('/play_pause', methods=['POST'])
@login_required
def play_pause():
    pyautogui.press('playpause')  # Simulate Play/Pause media key
    return redirect(url_for('home'))

@app.route('/volume_up', methods=['POST'])
@login_required
def volume_up():
    pyautogui.press('volumeup')  # Simulate Volume Up key
    return redirect(url_for('home'))

@app.route('/volume_down', methods=['POST'])
@login_required
def volume_down():
    pyautogui.press('volumedown')  # Simulate Volume Down key
    return redirect(url_for('home'))

@app.route('/brightness_up', methods=['POST'])
@login_required
def brightness_up():
    sbc.set_brightness(sbc.get_brightness()[0] + 10)
    return redirect(url_for('home'))
 
@app.route('/brightness_down', methods=['POST'])
@login_required
def brightness_down():
    sbc.set_brightness(sbc.get_brightness()[0] - 10)
    return redirect(url_for('home'))

# Route to handle text input submission
@app.route('/submit_text', methods=['POST'])
@login_required
def submit_text():
    text = request.form['text_input']

    if text.upper() in [f"F{i}" for i in range(1, 13)]:
        # Simulate pressing the function key
        keyboard.press_and_release(text.lower())
    else:
        # If Control is toggled, simulate key combinations
        if toggle_keys["Control"]:
            for char in text:
                keyboard.press('ctrl')
                keyboard.press_and_release(char)
                keyboard.release('ctrl')
        else:
            for char in text:
                keyboard.write(char)
    
    
    
    return redirect(url_for('home'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stream", action="store_true",
                        help="Enable MJPEG streaming (/stream)")
    args = parser.parse_args()

    if args.stream:
        start_stream()
    app.run(host='0.0.0.0', port=1338)
