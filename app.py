from flask import Flask, render_template, request, redirect, url_for
import keyboard
import time

app = Flask(__name__)

# Dictionary to keep track of which keys are toggled (held down)
toggle_keys = {
    "Shift": False,
    "Control": False,
    "Alt": False
}

@app.route('/')
def home():
    return render_template('index.html', toggle_keys=toggle_keys)

# Route to handle key press events
@app.route('/press_key', methods=['POST'])
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



# Route to handle text input submission
@app.route('/submit_text', methods=['POST'])
def submit_text():
    text = request.form['text_input']
    
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
