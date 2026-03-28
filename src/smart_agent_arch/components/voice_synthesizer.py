import torch
import numpy as np
import scipy.io.wavfile
from pathlib import Path

try:
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
except ImportError:
    ParlerTTSForConditionalGeneration = None
    AutoTokenizer = None

from smart_agent_arch.tools_loader import export_tool

class VoiceSynthesizer:
    """
    Component 3: Super-Detailed Voice Synthesis.
    Generates high-quality speech where the voice characteristics are completely defined
    by text descriptions (e.g., 'A slow, deep voice like an old turtle speaking slowly.').
    """
    def __init__(self, model_id="parler-tts/parler-tts-mini-v1"):
        self.is_ready = bool(ParlerTTSForConditionalGeneration and AutoTokenizer)
        self.model_id = model_id
        self._model = None
        self._tokenizer = None
        self._description_tokenizer = None
        # Default device: CUDA if available, else CPU
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

    def _load_models(self):
        if not self._model and self.is_ready:
            print(f"Loading Parler-TTS Text-To-Speech Model ({self.model_id}) on {self.device}...")
            # We lazy-load the heavy model into VRAM
            self._model = ParlerTTSForConditionalGeneration.from_pretrained(self.model_id).to(self.device)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self._description_tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            print("Model loaded successfully.")

    @export_tool
    def synthesize_described_voice(self, text: str, voice_description: str = "A clear, natural human voice.", output_path: str = "output_speech.wav") -> str:
        """
        Synthesizes highly-detailed speech using the description of the speaker's voice.
        :param text: The exact sentence or paragraph to be spoken.
        :param voice_description: The physical description of how it should sound (e.g., "A deep, slow raspy voice like an ancient turtle speaking").
        :param output_path: The file path to save the generated .wav audio file.
        :return: Success message with the output file path.
        """
        if not self.is_ready:
            return "Error: Voice synthesis requires Parler-TTS package. Run: pip install git+https://github.com/huggingface/parler-tts.git torch transformers scipy numpy"
            
        try:
            # Lazy load models to save VRAM when not in use
            self._load_models()
        except Exception as e:
            return f"Error loading TTS models: {str(e)}\nPlease check your HuggingFace models cache and network connection."

        try:
            print(f"Synthesizing voice: '{voice_description}' for text: '{text[:20]}...'")
            
            # Tokenize the speaker voice description
            input_ids = self._description_tokenizer(voice_description, return_tensors="pt").input_ids.to(self.device)
            
            # Tokenize the actual text to be spoken
            prompt_input_ids = self._tokenizer(text, return_tensors="pt").input_ids.to(self.device)

            # Generate audio data
            generation = self._model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation.cpu().numpy().squeeze()
            
            # Save audio array to file
            sample_rate = self._model.config.sampling_rate
            scipy.io.wavfile.write(output_path, sample_rate, audio_arr)
            
            return f"Successfully generated incredibly detailed voice! Saved speech to {output_path}"
            
        except Exception as e:
            return f"Failed to synthesize voice: {str(e)}"
