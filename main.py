from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union
import re

app = FastAPI()

class InputData(BaseModel):
    text: str

class ResponseItem(BaseModel):
    type: str
    content: Union[str, None] = None
    url: Union[str, None] = None
    alt_text: Union[str, None] = None

class ResponseOutput(BaseModel):
    responses: List[ResponseItem]

def parse_input(input_text: str) -> List[ResponseItem]:
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
            accumulated_text += line + " "
    
    # Append any remaining text after the last image
    if accumulated_text.strip():
        responses.append({"type": "text", "content": accumulated_text.strip()})
    
    return responses

@app.post("/generate-response", response_model=ResponseOutput)
async def generate_response(data: InputData):
    # Parse the input text from the "text" field and generate responses
    parsed_responses = parse_input(data.text)
    
    # Return the parsed response in the required JSON format
    return ResponseOutput(responses=parsed_responses)
