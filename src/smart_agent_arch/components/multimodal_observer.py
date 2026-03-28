import os
import io
import time
from pathlib import Path
from PIL import Image

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from smart_agent_arch.tools_loader import export_tool

class MultimodalObserver:
    """
    Component 1: Real-time Multimodal (Video/Audio/Image -> Text).
    Takes a file path and converts its content into highly detailed description
    to feed into text-only agents.
    """
    
    def __init__(self, api_key: str = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        self.is_ready = False
        if key and genai:
            genai.configure(api_key=key)
            # Use gemini-1.5-pro for advanced multimodal reasoning
            self.vision_model = genai.GenerativeModel('gemini-1.5-pro')
            self.is_ready = True

    @export_tool
    def describe_media(self, file_path: str, instruction: str = "Describe exactly what you see/hear in maximum detail. Include emotions, actions, setting, and potential context.") -> str:
        """
        Converts an image, audio, or video file into a highly detailed text description.
        :param file_path: Path to the media file (.jpg, .png, .mp3, .mp4, etc.)
        :param instruction: Specific prompt asking what to extract from the media.
        :return: Detailed text description of the media.
        """
        if not self.is_ready:
            return "Error: MultimodalObserver requires 'google-generativeai' package and GEMINI_API_KEY environment variable. Run: pip install google-generativeai"

        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} not found."

        ext = path.suffix.lower()
        
        try:
            # For images
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                img = Image.open(path)
                response = self.vision_model.generate_content([instruction, img])
                return response.text
                
            # For Audio / Video
            elif ext in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.webm', '.ogg']:
                print(f"Uploading {ext.upper()} to Multimodal Engine...")
                # Upload using File API
                uploaded_file = genai.upload_file(path=str(path))
                
                # Wait for processing if video
                if ext in ['.mp4', '.avi', '.mov', '.webm']:
                    while uploaded_file.state.name == 'PROCESSING':
                        print("Waiting for video to be processed by Gemini...")
                        time.sleep(2)
                        uploaded_file = genai.get_file(uploaded_file.name)
                        if uploaded_file.state.name == 'FAILED':
                            return "Error: Video processing failed."

                print("Generating detailed multimodal description...")
                response = self.vision_model.generate_content([uploaded_file, instruction])
                
                # Clean up cloud file
                genai.delete_file(uploaded_file.name)
                
                return response.text
            else:
                return f"Error: Unsupported file format {ext} for MultimodalObserver."
                
        except Exception as e:
            return f"Error analyzing media: {str(e)}"

