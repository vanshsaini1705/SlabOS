import pytest
from pathlib import Path

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


def test_storage_paths_stay_inside_media_root(tmp_path):
    from slabos.storage.paths import StoragePaths

    storage = StoragePaths(str(tmp_path))

    target, base = storage.resolve("folder/file.txt")
    assert Path(target) == (tmp_path / "folder/file.txt").resolve()
    assert Path(base) == tmp_path.resolve()


def test_storage_paths_reject_escape(tmp_path):
    from slabos.storage.paths import StoragePaths
    import pytest

    storage = StoragePaths(str(tmp_path))

    with pytest.raises(PermissionError):
        storage.resolve("../outside.txt")


def test_storage_paths_reject_absolute_escape(tmp_path):
    from slabos.storage.paths import StoragePaths
    import pytest

    storage = StoragePaths(str(tmp_path))

    with pytest.raises(PermissionError):
        storage.resolve("/tmp/outside.txt")


def test_storage_paths_allow_nested_paths(tmp_path):
    from slabos.storage.paths import StoragePaths

    storage = StoragePaths(str(tmp_path))

    target, base = storage.resolve("a/b/c.txt")
    assert Path(target) == (tmp_path / "a/b/c.txt").resolve()
    assert Path(base) == tmp_path.resolve()


def test_storage_service_file_operations(tmp_path):
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageService

    service = StorageService(StoragePaths(str(tmp_path)))

    (tmp_path / "old.txt").write_text("hello")

    folders, files = service.list_directory("")
    assert folders == []
    assert files == ["old.txt"]

    service.create_folder("", "docs")
    assert (tmp_path / "docs").is_dir()

    service.rename("old.txt", "new.txt")
    assert not (tmp_path / "old.txt").exists()
    assert (tmp_path / "new.txt").read_text() == "hello"

    assert service.get_file("new.txt") == str((tmp_path / "new.txt").resolve())

    service.delete("new.txt")
    assert not (tmp_path / "new.txt").exists()

    service.delete("docs")
    assert not (tmp_path / "docs").exists()


def test_storage_service_rejects_unsafe_names(tmp_path):
    import pytest
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageService

    service = StorageService(StoragePaths(str(tmp_path)))

    with pytest.raises(PermissionError):
        service.create_folder("", "../escape")

    (tmp_path / "safe.txt").write_text("hello")

    with pytest.raises(PermissionError):
        service.rename("safe.txt", "../escape.txt")

    with pytest.raises(PermissionError):
        service.get_file("../outside.txt")


def test_storage_upload_filename_validation(tmp_path):
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageUploadService, UploadValidationError

    service = StorageUploadService(StoragePaths(str(tmp_path)))

    assert service.validate_filename("photo.jpg") == "photo.jpg"

    with pytest.raises(UploadValidationError):
        service.validate_filename("")

    with pytest.raises(UploadValidationError):
        service.validate_filename("../photo.jpg")

    with pytest.raises(UploadValidationError):
        service.validate_filename("/tmp/photo.jpg")


def test_storage_upload_destination_validation(tmp_path):
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageUploadService, UploadValidationError

    service = StorageUploadService(StoragePaths(str(tmp_path)))
    (tmp_path / "uploads").mkdir()

    destination = service.get_destination("uploads", "photo.jpg")
    assert destination == (tmp_path / "uploads/photo.jpg").resolve()

    with pytest.raises(UploadValidationError):
        service.get_destination("../outside", "photo.jpg")


def test_storage_upload_writes_file_atomically(tmp_path):
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageUploadService

    class FakeUpload:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        async def read(self, _size):
            return next(self.chunks, b"")

    service = StorageUploadService(
        StoragePaths(str(tmp_path)),
        max_size_bytes=1024,
    )

    (tmp_path / "uploads").mkdir()

    import asyncio

    result = asyncio.run(service.save_upload(
        FakeUpload([b"hello ", b"SlabOS"]),
        "uploads",
        "test.txt",
    ))

    assert result == (tmp_path / "uploads/test.txt").resolve()
    assert result.read_bytes() == b"hello SlabOS"
    assert not list((tmp_path / "uploads").glob("*.upload"))


def test_storage_upload_rejects_oversized_file_and_cleans_temp(tmp_path):
    from slabos.storage.paths import StoragePaths
    from slabos.storage.service import StorageUploadService, UploadTooLargeError

    class FakeUpload:
        def __init__(self, chunks):
            self.chunks = iter(chunks)

        async def read(self, _size):
            return next(self.chunks, b"")

    service = StorageUploadService(
        StoragePaths(str(tmp_path)),
        max_size_bytes=5,
    )

    import asyncio

    with pytest.raises(UploadTooLargeError):
        asyncio.run(service.save_upload(
            FakeUpload([b"1234", b"56"]),
            "",
            "too-big.txt",
        ))

    assert not (tmp_path / "too-big.txt").exists()
    assert not list(tmp_path.glob("*.upload"))
