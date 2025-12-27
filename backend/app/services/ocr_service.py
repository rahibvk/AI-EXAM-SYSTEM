import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm_vision = ChatOpenAI(model="gpt-4o", temperature=0.0)

class OCRService:
    @staticmethod
    async def transcribe_image(image_path: str) -> str:
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
