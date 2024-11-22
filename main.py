import os
import requests
from requests.auth import HTTPBasicAuth
import base64
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio Media Download and Encode
def download_and_encode_twilio_image(media_url):
    """
    Downloads an image from a Twilio media URL and converts it to base64.

    Args:
        media_url (str): Twilio media URL for the image

    Returns:
        str: Base64 encoded image data, or None if download fails
    """
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.error("Twilio credentials not found in environment variables")
        return None

    try:
        response = requests.get(
            media_url,
            stream=True,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        )

        if response.status_code == 200:
            base64_image = base64.b64encode(response.content).decode("utf-8")
            return base64_image
        else:
            logger.error(f"Failed to download media: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error occurred while downloading Twilio media: {str(e)}")
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

# Endpoints
@app.route("/process-image", methods=["POST"])
def process_twilio_image():
    media_url = request.form.get("MediaUrl0")

    if not media_url:
        return jsonify({"error": "No media URL provided"}), 400

    base64_image = download_and_encode_twilio_image(media_url)

    if base64_image:
        return jsonify({"base64_image": base64_image, "status": "success"})
    else:
        return jsonify({"error": "Failed to download or encode image", "status": "failure"}), 500


@app.route("/get-image", methods=["POST"])
def get_facebook_image():
    media_id = request.json.get("media_id")

    if not media_id:
        return jsonify({"error": "Media ID is required"}), 400

    base64_image = download_and_encode_facebook_image(media_id)

    if base64_image:
        return jsonify({"base64_image": base64_image, "status": "success"})
    else:
        return jsonify({"error": "Failed to download or encode image", "status": "failure"}), 500
    
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


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    host = os.getenv("HOST")
    app.run(host=host, port=port, debug=True)
