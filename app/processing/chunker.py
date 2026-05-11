import uuid

from app.models.document import CodeDocument
from app.models.chunk import CodeChunk

from app.processing.python_parser import (
    PythonParser,
)


CHUNK_SIZE = 80
CHUNK_OVERLAP = 20


class CodeChunker:
    def __init__(self):
        self.python_parser = PythonParser()

    def chunk_document(
        self,
        document: CodeDocument,
    ) -> list[CodeChunk]:
        if document.extension == ".py":
            structured_chunks = (
                self._chunk_python_document(
                    document
                )
            )

            if structured_chunks:
                return structured_chunks

        return self._default_chunking(document)

    def _chunk_python_document(
        self,
        document: CodeDocument,
    ) -> list[CodeChunk]:
        code_blocks = (
            self.python_parser.extract_code_blocks(
                document
            )
        )

        chunks = []

        for index, block in enumerate(
            code_blocks
        ):
            chunk = CodeChunk(
                chunk_id=str(uuid.uuid4()),
                content=block["content"],
                file_path=document.file_path,
                start_line=block["start_line"],
                end_line=block["end_line"],
                chunk_type=block["type"],
                symbol_name=block["name"],
                chunk_index=index,
            )

            chunks.append(chunk)

        return chunks

    def _default_chunking(
        self,
        document: CodeDocument,
    ) -> list[CodeChunk]:
        chunks = []

        lines = document.content.splitlines()

        start = 0
        chunk_index = 0

        while start < len(lines):
            end = start + CHUNK_SIZE

            chunk_lines = lines[start:end]

            chunk_content = "\n".join(
                chunk_lines
            )

            chunk = CodeChunk(
                chunk_id=str(uuid.uuid4()),
                content=chunk_content,
                file_path=document.file_path,
                start_line=start + 1,
                end_line=min(
                    end,
                    len(lines),
                ),
                chunk_index=chunk_index,
            )

            chunks.append(chunk)

            chunk_index += 1

            start += (
                CHUNK_SIZE
                - CHUNK_OVERLAP
            )

        return chunks

    def chunk_documents(
        self,
        documents: list[CodeDocument],
    ) -> list[CodeChunk]:
        all_chunks = []

        for document in documents:
            chunks = self.chunk_document(
                document
            )

            all_chunks.extend(chunks)

        return all_chunks