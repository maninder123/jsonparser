import base64
from flask import Flask, request, jsonify
import requests



app = Flask(__name__)

@app.route('/get_image', methods=['POST'])
def get_image():
    media_id = request.json.get('media_id')
    headers = {
            "Authorization": f"Bearer EAAPHZC1SC48ABO9LD4Gu4NZCO6lpWSwkgAWYEgPWXdT8wzCSaLokUlISD7hOgMxzZCXr8RXZCHCOdbUpNakCMQsWuDKiDIH9yZCZAIxKgcP65u3gOqOk4cjrvbdZBFNTBDT6fRweAO1YKEuwRUKLDzkvVcwShWyxcwPS6DMbBHuVzGO82BH7E3rRXkRZB0SnlEZA9kAZDZD",
            # "User-Agent": self.user_agent
        }
    if not media_id:
        return jsonify({'error': 'Media ID is required'}), 400

    try:
        # Call WhatsApp media retrieval URL to get the media URL
        media_url_response = requests.get(f'https://graph.facebook.com/v19.0/{media_id}?phone_number_id=359029663964957',headers=headers)
        media_url_data = media_url_response.json()
        media_url = media_url_data.get('url', None)

        if not media_url:
            return jsonify({'error': 'Failed to retrieve media URL'}), 400

        # Call WhatsApp media download API to get the image
        image_response = requests.get(media_url,headers=headers)
        image_data = image_response.content

        # Convert image data to Base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        return jsonify({'base64_image': base64_image})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="143.244.132.143", port=8084)