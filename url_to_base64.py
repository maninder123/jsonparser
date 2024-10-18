from flask import Flask, request, jsonify
import base64
import requests

app = Flask(__name__)

def image_url_to_base64(image_url):
    try:
        # Send a GET request to the image URL
        response = requests.get(image_url)
        # Check if the request was successful
        if response.status_code == 200:
            # Encode the image content to base64
            base64_image = base64.b64encode(response.content).decode('utf-8')
            return base64_image
        else:
            return None
    except Exception as e:
        return None

@app.route('/convert-image', methods=['POST'])
def convert_image():
    data = request.json
    if 'image_url' not in data:
        return jsonify({"error": "Missing 'image_url' field"}), 400

    image_url = data['image_url']
    base64_image = image_url_to_base64(image_url)

    if base64_image:
        base64_img = "data:image/png;base64," + base64_image
        return base64_img
    else:
        return jsonify({"error": "Failed to convert image"}), 400


if __name__ == '__main__':
    app.run(host="143.244.132.143", port=8085)