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
