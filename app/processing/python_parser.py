import ast

from app.models.document import CodeDocument


class PythonParser:
    def __init__(self):
        pass

    def extract_code_blocks(
        self,
        document: CodeDocument,
    ) -> list[dict]:
        code_blocks = []

        try:
            tree = ast.parse(document.content)

            lines = document.content.splitlines()

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    start_line = node.lineno
                    end_line = node.end_lineno

                    block_content = "\n".join(
                        lines[
                            start_line - 1 : end_line
                        ]
                    )

                    code_blocks.append(
                        {
                            "type": type(node).__name__,
                            "name": node.name,
                            "content": block_content,
                            "start_line": start_line,
                            "end_line": end_line,
                        }
                    )

        except SyntaxError:
            return []

        return code_blocks