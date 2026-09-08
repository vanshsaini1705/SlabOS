import json

import httpx
import pytest

from slabos.ai.client import OllamaClient


class FakeStreamResponse:
    def __init__(self, lines):
        self.lines = lines

    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        for line in self.lines:
            yield line

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.request_args = None

    def stream(self, method, url, json):
        self.request_args = (method, url, json)
        return self.response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.anyio
async def test_stream_generates_text_events():
    client = OllamaClient()

    response = FakeStreamResponse([
        json.dumps({"response": "Hello", "done": False}),
        json.dumps({"response": " world", "done": True}),
    ])
    fake_client = FakeAsyncClient(response)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "slabos.ai.client.httpx.AsyncClient",
            lambda timeout: fake_client,
        )

        events = [
            event
            async for event in client.stream(
                "Say hello",
                "llama3.2:1b",
            )
        ]

    assert events == [
        'data: {"text": "Hello"}\n\n',
        'data: {"text": " world"}\n\n',
    ]

    method, url, payload = fake_client.request_args
    assert method == "POST"
    assert url == "http://localhost:11434/api/generate"
    assert payload == {
        "model": "llama3.2:1b",
        "prompt": "Say hello",
        "stream": True,
    }


@pytest.mark.anyio
async def test_stream_includes_images_when_provided():
    client = OllamaClient()

    response = FakeStreamResponse([
        json.dumps({"response": "Vision result", "done": True}),
    ])
    fake_client = FakeAsyncClient(response)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "slabos.ai.client.httpx.AsyncClient",
            lambda timeout: fake_client,
        )

        events = [
            event
            async for event in client.stream(
                "Describe image",
                "llava:latest",
                ["base64-image"],
            )
        ]

    assert events == ['data: {"text": "Vision result"}\n\n']

    _, _, payload = fake_client.request_args
    assert payload["images"] == ["base64-image"]


@pytest.mark.anyio
async def test_stream_returns_error_event_for_http_failure():
    client = OllamaClient()

    class FailingAsyncClient:
        def stream(self, method, url, json):
            raise httpx.ConnectError("connection failed")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "slabos.ai.client.httpx.AsyncClient",
            lambda timeout: FailingAsyncClient(),
        )

        events = [
            event
            async for event in client.stream(
                "Hello",
                "llama3.2:1b",
            )
        ]

    assert len(events) == 1
    assert json.loads(events[0].removeprefix("data: ").strip())["error"] == "connection failed"
