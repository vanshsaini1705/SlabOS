import os
import tempfile
from pathlib import Path

from .paths import StoragePaths


class StorageService:
    """Own SlabOS filesystem operations behind a storage boundary."""

    def __init__(self, paths: StoragePaths):
        self.paths = paths

    def list_directory(self, subpath: str = "") -> tuple[list[str], list[str]]:
        """Return sorted (folders, files) for a storage directory."""
        target, _ = self.paths.resolve(subpath)

        if not Path(target).is_dir():
            raise PermissionError("Forbidden Path")

        folders = []
        files = []
        mounted_usb_names = set()

        if subpath == "":
            from .paths import get_usb_drives
            mounted_usb_names = set(get_usb_drives())

        for item in Path(target).iterdir():
            if item.is_dir():
                if item.name in mounted_usb_names:
                    continue
                folders.append(item.name)
            elif item.is_file():
                files.append(item.name)

        return sorted(folders), sorted(files)

    def get_file(self, filepath: str) -> str:
        """Resolve a downloadable file and require it to exist."""
        target, _ = self.paths.resolve(filepath)

        if not Path(target).is_file():
            raise PermissionError("Forbidden Path")

        return target

    def create_folder(self, subpath: str, folder_name: str) -> str:
        """Create a folder inside the selected storage root."""
        target, base = self.paths.resolve(subpath)
        new_dir = (Path(target) / folder_name).resolve()
        base_path = Path(base).resolve()

        if not new_dir.is_relative_to(base_path):
            raise PermissionError("Forbidden Path")

        new_dir.mkdir(parents=True, exist_ok=True)
        return str(new_dir)

    def delete(self, target_path: str) -> None:
        """Delete a file or directory, but never a storage root."""
        target, base = self.paths.resolve(target_path)
        target_path_obj = Path(target)
        base_path = Path(base).resolve()

        if target_path_obj == base_path:
            raise PermissionError("Forbidden Path")

        if target_path_obj.is_dir():
            import shutil
            shutil.rmtree(target_path_obj)
        elif target_path_obj.is_file():
            target_path_obj.unlink()

    def rename(self, old_path: str, new_name: str) -> str:
        """Rename an item without allowing path escape through new_name."""
        source, base = self.paths.resolve(old_path)
        source_path = Path(source)
        base_path = Path(base).resolve()

        destination = (source_path.parent / new_name).resolve()

        if not destination.is_relative_to(base_path):
            raise PermissionError("Forbidden Path")

        source_path.rename(destination)
        return str(destination)


class UploadTooLargeError(Exception):
    """Raised when an upload exceeds the configured size limit."""


class UploadValidationError(Exception):
    """Raised when an uploaded filename or destination is invalid."""


class StorageUploadService:
    """Handle bounded, atomic file uploads inside a storage root."""

    def __init__(self, paths: StoragePaths, max_size_bytes: int = 100 * 1024 * 1024):
        self.paths = paths
        self.max_size_bytes = max_size_bytes

    def validate_filename(self, filename: str) -> str:
        """Validate and normalize a client-provided filename."""
        if not isinstance(filename, str):
            raise UploadValidationError("Invalid filename")

        filename = filename.strip()

        if not filename:
            raise UploadValidationError("Invalid filename")

        name = Path(filename).name

        if name != filename or name in {".", ".."}:
            raise UploadValidationError("Invalid filename")

        return name

    def get_destination(self, subpath: str, filename: str) -> Path:
        """Return a safe destination path inside the selected storage root."""
        safe_name = self.validate_filename(filename)

        try:
            target_dir, base = self.paths.resolve(subpath)
        except PermissionError as exc:
            raise UploadValidationError("Invalid destination") from exc

        target_dir_path = Path(target_dir)
        base_path = Path(base).resolve()

        if not target_dir_path.is_dir():
            raise UploadValidationError("Invalid destination")

        destination = (target_dir_path / safe_name).resolve()

        if not destination.is_relative_to(base_path):
            raise UploadValidationError("Invalid destination")

        return destination

    async def save_upload(self, file, subpath: str, filename: str) -> Path:
        """Stream an upload to a temporary file and atomically finalize it."""
        destination = self.get_destination(subpath, filename)
        temp_path = None
        total_size = 0

        fd, temp_path = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".upload",
            dir=str(destination.parent),
        )

        try:
            with os.fdopen(fd, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)

                    if total_size > self.max_size_bytes:
                        raise UploadTooLargeError("Upload exceeds the maximum size")

                    buffer.write(chunk)

                buffer.flush()
                os.fsync(buffer.fileno())

            os.replace(temp_path, destination)
            temp_path = None
            return destination

        finally:
            if temp_path is not None:
                try:
                    Path(temp_path).unlink()
                except FileNotFoundError:
                    pass
