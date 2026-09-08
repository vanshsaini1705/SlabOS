import os
from pathlib import Path

import psutil


def get_usb_drives() -> dict[str, str]:
    """Return already-mounted external/USB storage locations."""
    usbs: dict[str, str] = {}

    try:
        for part in psutil.disk_partitions(all=False):
            if os.name == "nt" and part.device != "C:\\":
                usbs[f"USB_Drive_{part.device[0]}"] = part.mountpoint
            elif os.name != "nt" and (
                "/media/" in part.mountpoint
                or "/mnt/" in part.mountpoint
                or "/Volumes/" in part.mountpoint
            ):
                usbs[f"USB_{os.path.basename(part.mountpoint)}"] = part.mountpoint
    except OSError:
        pass

    return usbs


class StoragePaths:
    """Resolve SlabOS storage paths without escaping their storage root."""

    def __init__(self, media_dir: str):
        self.media_dir = Path(media_dir).resolve()

    def resolve(self, subpath: str) -> tuple[str, str]:
        """Resolve a vault-relative path and return (target, base_dir)."""
        subpath = subpath or ""

        for usb_name, usb_path in get_usb_drives().items():
            if subpath == usb_name or subpath.startswith(usb_name + "/"):
                relative = subpath[len(usb_name):].lstrip("/")
                base = Path(usb_path).resolve()
                target = (base / relative).resolve()
                if not target.is_relative_to(base):
                    raise PermissionError("Forbidden Path")
                return str(target), str(base)

        target = (self.media_dir / subpath).resolve()
        if not target.is_relative_to(self.media_dir):
            raise PermissionError("Forbidden Path")

        return str(target), str(self.media_dir)
