import ast

from app.models.document import CodeDocument


class DependencyExtractor:
    def __init__(self):
        pass

    def extract_dependencies(
        self,
        document: CodeDocument,
    ) -> list[str]:
        dependencies = []

        try:
            tree = ast.parse(
                document.content
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(
                            alias.name
                        )

                elif isinstance(
                    node,
                    ast.ImportFrom,
                ):
                    module = node.module

                    if module:
                        dependencies.append(
                            module
                        )

        except SyntaxError:
            return []

        return list(set(dependencies))