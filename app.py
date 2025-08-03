# ✅ app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"


def extract_message(image, key):
    binary_message = ""
    pixels = image.convert("RGB").load()
    width, height = image.size

    key_bin = ''.join(format(ord(c), '08b') for c in key)
    message_bits = ""

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            lsb = r & 1
            message_bits += str(lsb)

            if len(message_bits) % 8 == 0:
                byte = message_bits[-8:]
                if byte == '00000000':  # Null terminator
                    binary_message = message_bits[:-8]
                    break
        else:
            continue
        break

    chars = [binary_message[i:i + 8] for i in range(0, len(binary_message), 8)]
    message = ''.join([chr(int(b, 2)) for b in chars])
    return message


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/decrypt", methods=["POST"])
def decrypt():
    if 'image' not in request.files:
        flash("No image file uploaded")
        return redirect(url_for("index"))

    image_file = request.files["image"]
    key = request.form.get("key", "")

    if not key:
        flash("Key is required")
        return redirect(url_for("index"))

    try:
        image = Image.open(image_file.stream)
        message = extract_message(image, key)
        return render_template("index.html", decrypted_message=message)
    except Exception as e:
        flash("Error during decryption: " + str(e))
        return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
