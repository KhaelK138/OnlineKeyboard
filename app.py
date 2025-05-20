from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import pyautogui
import keyboard
import screen_brightness_control as sbc
import time
from functools import wraps

app = Flask(__name__)
app.secret_key = ""  # Replace with a strong secret key

# Hardcoded password
PASSWORD = ""

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

# Endpoint to serve login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == PASSWORD:
            session['auth_token'] = 'authenticated'  # Set a session token
            return redirect(url_for('home'))  # Redirect to the main page after login
        else:
            return "Invalid password", 401  # Return an error for invalid password
    return render_template('login.html')  # Serve the login page template

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
    app.run(host='0.0.0.0', port=1338)
