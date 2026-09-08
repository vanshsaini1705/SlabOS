from project import (
    recommend_ai_model,
    calculate_zram_size,
    verify_path_security,
    sanitize_mdns_hostname,
    generate_auth_pin,
    verify_api_pin,
)


def test_recommend_ai_model_low_ram():
    assert recommend_ai_model(4, False) == "llama3.2:1b"
    assert recommend_ai_model(4, True) == "qwen2.5:1.5b"


def test_recommend_ai_model_disk_safety():
    assert recommend_ai_model(8, False, 6) == ""


def test_calculate_zram_size():
    assert calculate_zram_size(4) == 2.0
    assert calculate_zram_size(32) == 8.0
    assert calculate_zram_size(-1) == 0.0


def test_verify_path_security(tmp_path):
    file_path = tmp_path / "safe.txt"
    file_path.write_text("hello")

    assert verify_path_security("safe.txt", str(tmp_path)) is True
    assert verify_path_security("../safe.txt", str(tmp_path)) is False
    assert verify_path_security("missing.txt", str(tmp_path)) is False


def test_sanitize_mdns_hostname():
    assert sanitize_mdns_hostname("My SlabOS_Node") == "my-slabos-node"
    assert sanitize_mdns_hostname("") == "slabos"


def test_generate_auth_pin():
    pin = generate_auth_pin()
    assert len(pin) == 4
    assert pin.isdigit()


def test_verify_api_pin():
    assert verify_api_pin("1234", "1234") is True
    assert verify_api_pin(" 1234 ", "1234") is True
    assert verify_api_pin("1234", "9999") is False
    assert verify_api_pin("", "1234") is False
    assert verify_api_pin(None, "1234") is False


def test_generate_auth_pin_behavior():
    pin = generate_auth_pin()
    assert len(pin) == 4
    assert pin.isdigit()

    pin = generate_auth_pin(6)
    assert len(pin) == 6
    assert pin.isdigit()

    fallback_pin = generate_auth_pin(0)
    assert len(fallback_pin) == 4
    assert fallback_pin.isdigit()


def test_auth_service_master_and_guest(tmp_path):
    from slabos.auth.service import AuthService
    from slabos.config.manager import ConfigManager

    manager = ConfigManager()
    manager.CONFIG_FILE = tmp_path / "slabos_config.json"
    manager.save({
        "master_pin": "1234",
        "default_media_dir": "./media",
        "guest_pins": {"5678": "active"},
    })

    auth = AuthService(manager)

    assert auth.authenticate("1234", "1234") == (True, True)
    assert auth.authenticate("5678", "1234") == (True, False)
    assert auth.authenticate("9999", "1234") == (False, False)


def test_auth_service_create_guest_pin(tmp_path):
    from slabos.auth.service import AuthService
    from slabos.config.manager import ConfigManager

    manager = ConfigManager()
    manager.CONFIG_FILE = tmp_path / "slabos_config.json"
    manager.save({
        "master_pin": "1234",
        "default_media_dir": "./media",
        "guest_pins": {},
    })

    auth = AuthService(manager)
    guest_pin = auth.create_guest_pin()

    assert len(guest_pin) == 4
    assert guest_pin.isdigit()

    config = manager.load_or_create()
    assert config["guest_pins"][guest_pin] == "active"
