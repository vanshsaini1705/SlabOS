import json

import pytest

import server


@pytest.mark.anyio
async def test_api_chat_uses_server_authoritative_active_model(monkeypatch):
    server.app.state.active_model = "server-model"

    monkeypatch.setattr(
        server,
        "check_access",
        lambda pin: (True, True),
    )

    captured = {}

    async def fake_stream(prompt, model_name, images=None):
        captured["prompt"] = prompt
        captured["model"] = model_name
        captured["images"] = images
        yield f"data: {json.dumps({'text': 'ok'})}\n\n"

    monkeypatch.setattr(server, "stream_ollama_generator", fake_stream)

    payload = server.ChatPayload(
        prompt="hello",
        model="client-selected-model",
        images=["image-data"],
    )

    response = await server.api_chat_stream(payload, "1234")

    assert response.media_type == "text/event-stream"
    chunks = [chunk async for chunk in response.body_iterator]
    assert chunks == ['data: {"text": "ok"}\n\n']
    assert captured == {
        "prompt": "hello",
        "model": "server-model",
        "images": ["image-data"],
    }
