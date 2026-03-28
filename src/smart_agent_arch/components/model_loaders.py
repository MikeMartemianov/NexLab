from pathlib import Path
from smart_agent_arch.tools_loader import export_tool

class LocalModelLoader:
    """
    Component: Ready-made Local Model Loaders.
    Simplifies launching agents with localized, offline execution via GGUF or Transformers.
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_models = {}

    @export_tool
    def load_gguf_model(self, model_path_or_name: str, n_ctx: int = 4096, n_gpu_layers: int = -1) -> str:
        """
        Loads a local GGUF model via llama-cpp-python for high-performance CPU/GPU inference.
        :param model_path_or_name: The file name in 'models/' directory or absolute path.
        :param n_ctx: Context window size (default 4096).
        :param n_gpu_layers: Number of layers to offload to GPU (-1 for all).
        :return: Success message and internal memory ID of the loaded model.
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            return "Error: llama-cpp-python is not installed. Run: pip install llama-cpp-python"
            
        path = Path(model_path_or_name)
        if not path.exists():
            path = self.models_dir / path.name
            if not path.exists():
                return f"Error: GGUF model file not found at {path}"

        try:
            print(f"Loading GGUF model: {path.name}...")
            llm = Llama(
                model_path=str(path),
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            model_id = f"gguf_{path.stem}"
            self._loaded_models[model_id] = llm
            return f"Successfully loaded GGUF model '{path.name}'. Ready for offline inference via ID: {model_id}"
        except Exception as e:
            return f"Failed to load GGUF model: {str(e)}"

    @export_tool
    def load_transformers_model(self, repo_id: str, load_in_4bit: bool = True) -> str:
        """
        Loads a HuggingFace model directly into GPU memory using the transformers library.
        :param repo_id: HuggingFace repository ID (e.g., 'meta-llama/Llama-3-8B-Instruct').
        :param load_in_4bit: Whether to use bitsandbytes 4-bit quantization to save VRAM.
        :return: Success message and internal memory ID.
        """
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            return "Error: transformers and torch are required. Run: pip install transformers torch"

        try:
            kwargs = {"device_map": "auto"}
            if load_in_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
                except ImportError:
                    pass

            print(f"Downloading/Loading HF model: {repo_id}...")
            tokenizer = AutoTokenizer.from_pretrained(repo_id)
            model = AutoModelForCausalLM.from_pretrained(repo_id, **kwargs)
            
            model_id = f"hf_{repo_id.replace('/', '_')}"
            self._loaded_models[model_id] = {"model": model, "tokenizer": tokenizer}
            return f"Successfully loaded HF model '{repo_id}'. 4-bit quantization: {load_in_4bit}. Ready via ID: {model_id}"
        except Exception as e:
            return f"Failed to load HuggingFace model: {str(e)}"
