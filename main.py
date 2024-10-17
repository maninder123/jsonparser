from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union
import re

app = FastAPI()

# Updated InputData class to match the input structure
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
    
    # Split input into lines
    lines = input_text.splitlines()
    
    # Regex to detect image URLs
    image_regex = r"(https?://\S+\.(?:jpg|jpeg|png|gif))"
    
    # Traverse through the lines and parse text and image URLs
    for line in lines:
        # Check if the line contains an image URL
        image_match = re.search(image_regex, line)
        if image_match:
            image_url = image_match.group(1)
            alt_text = "Image related to the product"  # Enhance alt text extraction
            responses.append({"type": "image", "url": image_url, "alt_text": alt_text})
        else:
            # If it's just a text line, append as a text response
            clean_text = line.strip()
            if clean_text:
                responses.append({"type": "text", "content": clean_text})
    
    return responses

@app.post("/generate-response", response_model=ResponseOutput)
async def generate_response(data: InputData):
    # Parse the input text from the "text" field and generate responses
    parsed_responses = parse_input(data.text)
    
    # Return the parsed response in the required JSON format
    return ResponseOutput(responses=parsed_responses)
