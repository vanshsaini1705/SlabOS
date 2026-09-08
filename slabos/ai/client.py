import json
from typing import AsyncGenerator, List

import httpx


class OllamaClient:
    """Async client for streaming generation from the local Ollama server."""

    OLLAMA_URL = "http://localhost:11434/api/generate"
    TIMEOUT_SECONDS = 120.0

    async def stream(
        self,
        prompt: str,
        model_name: str,
        images: List[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream Ollama generation results as Server-Sent Events."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
        }

        if images:
            payload["images"] = images

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            try:
                async with client.stream(
                    "POST",
                    self.OLLAMA_URL,
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        data = json.loads(line)
                        token = data.get("response", "")

                        yield f"data: {json.dumps({'text': token})}\n\n"

                        if data.get("done"):
                            break

            except httpx.HTTPError as exc:
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
