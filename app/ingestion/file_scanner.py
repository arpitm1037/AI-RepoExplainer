from pathlib import Path

from app.core.constants import (
    SUPPORTED_EXTENSIONS,
    IGNORED_DIRECTORIES,
    IGNORED_FILES,
)


class FileScanner:
    def __init__(self):
        pass

    def scan_repository(self, repo_path: Path) -> list[Path]:
        valid_files = []

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            if self._should_ignore(file_path):
                continue

            if file_path.suffix not in SUPPORTED_EXTENSIONS:
                continue

            valid_files.append(file_path)

        return valid_files

    def _should_ignore(self, file_path: Path) -> bool:
        path_parts = set(file_path.parts)

        if path_parts.intersection(IGNORED_DIRECTORIES):
            return True

        if file_path.name in IGNORED_FILES:
            return True

        return False