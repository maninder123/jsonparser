import base64
from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

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
    

# Function to parse input text and generate the responses
def parse_input(input_text):
    responses = []
    accumulated_text = ""
    
    # Split input into lines
    lines = input_text.splitlines()
    
    # Regex to detect image URLs
    image_regex = r"(https?://\S+\.(?:jpg|jpeg|png|gif))"
    
    for line in lines:
        # Check if the line contains an image URL
        image_match = re.search(image_regex, line)
        
        if image_match:
            # If there is accumulated text, append it as a text response
            if accumulated_text.strip():
                responses.append({"type": "text", "content": accumulated_text.strip()})
                accumulated_text = ""  # Reset accumulated text

            # Append the image URL as a separate response
            image_url = image_match.group(1)
            alt_text = "Image related to the product"  # You can enhance this as needed
            responses.append({"type": "image", "url": image_url, "alt_text": alt_text})
        else:
            # Accumulate the text until an image is found
            accumulated_text += line + "\n"
    
    # Append any remaining text after the last image
    if accumulated_text.strip():
        responses.append({"type": "text", "content": accumulated_text.strip()})
    
    return responses

# Flask route to handle POST request and return response
@app.route("/generate-response", methods=["POST"])
def generate_response():
    data = request.get_json()
    
    # Validate the input text
    if "text" not in data:
        return jsonify({"error": "Invalid input, 'text' field is required"}), 400
    
    # Parse the input text and generate responses
    parsed_responses = parse_input(data["text"])
    
    # Return the parsed response in JSON format
    return jsonify({"responses": parsed_responses})

@app.route('/get_image', methods=['POST'])
def get_image():
    media_id = request.json.get('media_id')

    # Get token from environment variable
    auth_token = os.getenv('AUTH_TOKEN')

    headers = {
            "Authorization": f"Bearer {auth_token}",
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
        # Prepend the data URI scheme and return it
        base64_img = "data:image/png;base64," + base64_image
        
        return base64_img
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
    app.run(host='0.0.0.0',debug=True,port='5011')

