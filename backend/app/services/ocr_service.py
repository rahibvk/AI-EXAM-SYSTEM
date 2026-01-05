"""
OCR Integration Service

Purpose:
    Converts images of handwritten student exams into machine-readable text.
    It leverages the GPT-4o Vision capabilities for high-accuracy transcription.

Key Assumptions:
    - Images are in standard formats (JPEG, PNG).
    - Handwritten text is legible enough for a human to read.
    - No external OCR library (like Tesseract) is used; purely LLM-based.

Constraints:
    - High cost per page (Vision tokens).
    - Latency (3-5 seconds per page).
"""
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Initialize Vision Model
# Temperature 0.0 is critical here to avoid hallucinations during transcription.
llm_vision = ChatOpenAI(model="gpt-4o", temperature=0.0)

class OCRService:
    @staticmethod
    async def transcribe_image(image_path: str) -> str:
        """
        Helper method to transcribe text from a local file path.

        Inputs:
            image_path (str): Absolute path to the image file.
        
        Outputs:
            str: Transcribed text content.
        """
        """
        Transcribe handwritten text from an image file path.
        """
        try:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            return await OCRService.transcribe_bytes(image_bytes)
        except Exception as e:
            print(f"OCR Failed for {image_path}: {e}")
            return "[Error during OCR processing]"

    @staticmethod
    async def transcribe_bytes(image_bytes: bytes) -> str:
        """
        Core function that sends image data to OpenAI Vision API.

        Inputs:
            image_bytes (bytes): Raw byte content of the image.

        Outputs:
            str: The verbatim text found in the image, preserving layout where possible.

        Side Effects:
            - Calling this function consumes API credits (Vision model).
        """
        """
        Transcribe handwritten text from raw image bytes.
        """
        try:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
                
            # Construct prompt for Vision model
            message = HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": "Transcribe the handwritten text from this image exactly as it appears. Include any header information like Names or IDs at the top. Do not add any commentary."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            )
            
            response = await llm_vision.ainvoke([message])
            return response.content
            
        except Exception as e:
            print(f"OCR Bytes Failed: {e}")
            raise e
