import base64
import requests
import json
from pathlib import Path
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, validator


class ImagePromptSchema(BaseModel):
    """Input for Vision Tool."""

    image_path_url: str = "The image path or URL."

    @validator("image_path_url")
    def validate_image_path_url(cls, v: str) -> str:
        if v.startswith("http"):
            return v

        path = Path(v)
        if not path.exists():
            raise ValueError(f"Image file does not exist: {v}")

        # Validate supported formats
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Unsupported image format. Supported formats: {valid_extensions}"
            )

        return v


class VinTool(BaseTool):
    name: str = "Vin Tool"
    description: str = (
        "This tool uses LLAVA model to extract text from an image."
    )
    args_schema: Type[BaseModel] = ImagePromptSchema

    @property


    def _run(self, **kwargs) -> str:
        try:
           # image_path_url = kwargs.get("image_path_url")
            image_path_url = "/Users/yzou/projects/crewai/vin_extract/vin.jpeg"
            if not image_path_url:
                return "Image Path or URL is required."

            # Validate input using Pydantic
            #ImagePromptSchema(image_path_url=image_path_url)

            prompt = "Extract text from the image"

            if image_path_url.startswith("http"):
                image_data = image_path_url
            else:
                try:
                    image_base64 = self._encode_image(image_path_url)
                    image_data = f"data:image/jpeg;base64,{image_base64}"
                except Exception as e:
                    return f"Error processing image: {str(e)}"

            request_json = {"model": "llava:7b", "prompt": prompt, "images": [image_base64], "stream": False}
            request_response = requests.post("http://localhost:11434/api/generate", json=request_json)
            response_json = json.loads(request_response.text)
            answer = response_json["response"]
            print(f"DEBUG: Extracted text: {answer}")  # Debugging

            #  the return from the LLAVA-7b model running locally is not reliable :
            #try 1: failed
            #  DEBUG:" The image shows a close-up of a vehicle's Vehicle Identification Number (VIN),
            # which is typically found on the driver's side door. The VIN number displayed on
            #  the sticker is not clearly visible, and any attempt to transcribe it would be
            #  purely speculative as it may not be readable due to the angle and quality of the image."

            #try 2: recognized 16 digit, treated as license plate
            # DEBUG: Extracted text:  The text in the image is a license plate number: "PB17 4JK 219"
            # and "546 418". However, the second set of numbers appears to be cut off or obscured.

            #try 3: recognized as VIN, but worse result
            # DEBUG: Extracted text:  The text in the image reads:
            #```
            #72017367
            #```
            #Please note that this is likely a vehicle('s Vehicle Identification Number (VIN),'
            #' which is typically used to identify individual vehicles.)

        # let's fake it...    , generated VIN from https://vingenerator.org/
            # answer = "the extracted VIN number from the image is 2B4FK55J9KR146695"
            return answer

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
