from unittest.mock import patch

from slabos.ai.model_manager import ModelManager


def test_recommend_ai_model_low_ram():
    manager = ModelManager()

    assert manager.recommend_ai_model(4, False) == "llama3.2:1b"
    assert manager.recommend_ai_model(4, True) == "qwen2.5:1.5b"


def test_recommend_ai_model_disk_safety():
    manager = ModelManager()

    assert manager.recommend_ai_model(8, False, 6) == ""


def test_get_installed_models():
    manager = ModelManager()

    class Result:
        stdout = "NAME            ID\nllama3.2:1b    abc\nqwen2.5:7b     def\n"

    with patch(
        "slabos.ai.model_manager.subprocess.run",
        return_value=Result(),
    ) as run_mock:
        models = manager.get_installed_models()

    assert models == ["llama3.2:1b", "qwen2.5:7b"]
    run_mock.assert_called_once_with(
        ["ollama", "list"],
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_installed_models_when_ollama_is_unavailable():
    manager = ModelManager()

    with patch(
        "slabos.ai.model_manager.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        assert manager.get_installed_models() == []


def test_check_vision_capabilities():
    manager = ModelManager()

    assert manager.check_vision_capabilities(["llama3.2:1b", "llava:latest"]) is True
    assert manager.check_vision_capabilities(["llama3.2:1b", "gemma2:2b"]) is False


def test_setup_ollama_model_success():
    manager = ModelManager()

    with patch(
        "slabos.ai.model_manager.shutil.which",
        return_value="/usr/bin/ollama",
    ), patch(
        "slabos.ai.model_manager.subprocess.run",
    ) as run_mock:

        assert manager.setup_ollama_model("llama3.2:1b") is True

    run_mock.assert_called_once_with(
        ["ollama", "pull", "llama3.2:1b"],
        check=True,
    )


def test_setup_ollama_model_when_ollama_is_missing():
    manager = ModelManager()

    with patch(
        "slabos.ai.model_manager.shutil.which",
        return_value=None,
    ), patch(
        "slabos.ai.model_manager.subprocess.run",
    ) as run_mock:

        assert manager.setup_ollama_model("llama3.2:1b") is False

    run_mock.assert_not_called()


def test_setup_ollama_model_when_pull_fails():
    manager = ModelManager()

    with patch(
        "slabos.ai.model_manager.shutil.which",
        return_value="/usr/bin/ollama",
    ), patch(
        "slabos.ai.model_manager.subprocess.run",
        side_effect=__import__("subprocess").CalledProcessError(1, ["ollama", "pull"]),
    ):

        assert manager.setup_ollama_model("llama3.2:1b") is False
