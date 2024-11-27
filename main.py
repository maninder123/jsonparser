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

# Utility Function: Twilio Media Download and Encode
def download_and_encode_twilio_image(media_url):
    '''
    Downloads an image from a Twilio media URL and converts it to base64.

    Args:
        media_url (str): Twilio media URL for the image.

    Returns:
        str: Base64 encoded image data, or None if download fails.
    '''
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
    '''
    Parses input text for plain text and image URLs and generates a structured response.

    Args:
        input_text (str): Input text containing plain text and/or image URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a parsed response 
              (either text or image).
    '''
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


# Flask Endpoint: Process Twilio Image
@app.route('/process-image', methods=['POST'])
def process_twilio_image():
    '''
    API Endpoint: /process-image
    ----------------------------
    Processes an image sent via Twilio by downloading it from the provided MediaUrl0,
    encoding it in base64 format, and returning the encoded image.

    Method: POST

    Request:
        - Form Data:
            - MediaUrl0 (string): The URL of the image sent via Twilio.

    Responses:
        - 200 OK: Base64 encoded image string.
        - 400 Bad Request: Error for missing or invalid MediaUrl0.
        - 500 Internal Server Error: Error for download or encode failure.
    '''
    media_url = request.form.get('MediaUrl0')
    
    if not media_url:
        return jsonify({
            "error": "No media URL provided",
            "status": "failure"
        }), 400
       # Download and encode the image
    base64_image = download_and_encode_twilio_image(media_url)
    
    if base64_image:
        return f"data:image/png;base64,{base64_image}"
    else:
        return jsonify({
            "error": "Failed to download or encode image",
            "status": "failure"
        }), 500

    
# Flask Endpoint: Generate Response
@app.route("/generate-response", methods=["POST"])
def generate_response():
    '''
    API Endpoint: /generate-response
    --------------------------------
    Parses the input text for image URLs and plain text, generating a structured 
    JSON response.

    Method: POST

    Request:
        - JSON Body:
            {
                "text": "<input_text>"
            }

    Responses:
        - 200 OK: Structured JSON response containing text and images.
        - 400 Bad Request: Error for missing or invalid input text.
    '''
    data = request.get_json()
    # Validate the input text
    if "text" not in data:
        return jsonify({"error": "Invalid input, 'text' field is required"}), 400
      # Parse the input text and generate responses
    parsed_responses = parse_input(data["text"])
     # Return the parsed response in JSON format
    return jsonify({"responses": parsed_responses})


# Main Entry Point
if __name__ == "__main__":
    '''
    Main Entry Point for the Flask Application
    ------------------------------------------
    Configures and starts the Flask server using environment variables for host 
    and port.
    '''
    port = int(os.getenv("PORT"))
    host = os.getenv("HOST")
    app.run(host=host, port=port, debug=True)
