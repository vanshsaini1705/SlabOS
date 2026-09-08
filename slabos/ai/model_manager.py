import shutil
import subprocess


class ModelManager:
    """Manage local AI model selection and Ollama model operations."""

    SAFETY_BUFFER_GB = 5.0
    MAX_ZRAM_CAP_GB = 8.0
    VISION_KEYWORDS = [
        "llava",
        "qwen2-vl",
        "moondream",
        "vision",
    ]

    def recommend_ai_model(
        self,
        ram_gb: float,
        has_gpu: bool,
        disk_free_gb: float = 50.0,
    ) -> str:
        """Determine an AI model suitable for available system resources."""
        if disk_free_gb < (2.0 + self.SAFETY_BUFFER_GB):
            return ""

        if ram_gb < 6.0:
            return "qwen2.5:1.5b" if has_gpu else "llama3.2:1b"

        if ram_gb < 12.0:
            if disk_free_gb >= (5.0 + self.SAFETY_BUFFER_GB):
                return "qwen2.5:7b" if has_gpu else "gemma2:2b"
            return "qwen2.5:1.5b" if has_gpu else "llama3.2:1b"

        if ram_gb < 16.0:
            if disk_free_gb >= (5.0 + self.SAFETY_BUFFER_GB):
                return "deepseek-r1:7b" if has_gpu else "llama3.2:3b"
            return "gemma2:2b"

        if disk_free_gb >= (5.0 + self.SAFETY_BUFFER_GB):
            return "deepseek-r1:7b" if has_gpu else "llama3:8b"

        return "llama3.2:3b"

    def get_installed_models(self) -> list:
        """Query the local Ollama instance for installed models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n")[1:]
            return [line.split()[0] for line in lines if line]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def check_vision_capabilities(self, models: list) -> bool:
        """Check whether installed models expose multimodal vision support."""
        return any(
            any(keyword in model.lower() for keyword in self.VISION_KEYWORDS)
            for model in models
        )

    def setup_ollama_model(self, model_name: str) -> bool:
        """Download and verify an Ollama model."""
        if not shutil.which("ollama"):
            print(
                "\n[!] CRITICAL: Ollama binary not found. "
                "Install from https://ollama.com/"
            )
            return False

        print(f"\n[System] Verifying/Downloading model: {model_name}...")

        try:
            subprocess.run(["ollama", "pull", model_name], check=True)
            print(
                f"[bold green]✔ Node '{model_name}' is primed![/bold green]"
            )
            return True
        except subprocess.CalledProcessError:
            return False
