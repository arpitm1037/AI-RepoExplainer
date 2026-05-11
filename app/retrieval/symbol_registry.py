from app.models.chunk import CodeChunk


class SymbolRegistry:
    def __init__(self):
        self.symbols: dict = {}

    def register_chunks(
        self,
        chunks: list[CodeChunk],
    ):
        for chunk in chunks:
            if not chunk.symbol_name:
                continue

            self.symbols[
                chunk.symbol_name
            ] = {
                "chunk_id": (
                    chunk.chunk_id
                ),
                "file_path": (
                    chunk.file_path
                ),
                "chunk_type": (
                    chunk.chunk_type
                ),
                "start_line": (
                    chunk.start_line
                ),
                "end_line": (
                    chunk.end_line
                ),
            }

    def get_symbol(
        self,
        symbol_name: str,
    ):
        return self.symbols.get(
            symbol_name
        )

    def search_symbols(
        self,
        query: str,
    ):
        matches = []

        query_lower = query.lower()

        for (
            symbol_name,
            metadata,
        ) in self.symbols.items():
            if (
                query_lower
                in symbol_name.lower()
            ):
                matches.append(
                    {
                        "symbol_name": (
                            symbol_name
                        ),
                        "metadata": metadata,
                    }
                )

        return matches

    def restore_symbols(
        self,
        symbols: dict,
    ):
        self.symbols = {}

        if not symbols:
            return

        for (
            symbol_name,
            metadata,
        ) in symbols.items():
            if not isinstance(
                metadata,
                dict,
            ):
                continue

            self.symbols[
                str(symbol_name)
            ] = {
                "chunk_id": metadata.get(
                    "chunk_id"
                ),
                "file_path": str(
                    metadata.get(
                        "file_path",
                        "",
                    )
                ),
                "chunk_type": metadata.get(
                    "chunk_type"
                ),
                "start_line": int(
                    metadata.get(
                        "start_line"
                    )
                    or 0
                ),
                "end_line": int(
                    metadata.get(
                        "end_line"
                    )
                    or 0
                ),
            }