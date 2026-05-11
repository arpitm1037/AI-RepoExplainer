from pathlib import Path

from app.models.document import CodeDocument

from app.processing.dependency_extractor import (
    DependencyExtractor,
)


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".md",
}


class FileLoader:
    def __init__(self):
        self.dependency_extractor = (
            DependencyExtractor()
        )

    def load_file(
        self,
        file_path: str,
    ) -> CodeDocument | None:
        path = Path(file_path)

        try:
            content = path.read_text(
                encoding="utf-8"
            )

            document = CodeDocument(
                content=content,
                file_path=str(path),
                extension=path.suffix,
                size=path.stat().st_size,
            )

            if document.extension == ".py":
                dependencies = (
                    self.dependency_extractor.extract_dependencies(
                        document
                    )
                )

                document.dependencies = (
                    dependencies
                )

            return document

        except Exception as error:
            print(
                f"Failed to load {file_path}: {error}"
            )

            return None

    def load_files(
        self,
        file_paths: list[str],
    ) -> list[CodeDocument]:
        documents = []

        for file_path in file_paths:
            document = self.load_file(
                file_path
            )

            if document:
                documents.append(document)

        return documents