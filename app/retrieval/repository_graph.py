import ast

from app.models.document import (
    CodeDocument,
)


class RepositoryGraph:
    def __init__(self):
        self.graph = {}

        self.importance_scores = {}

    def build_graph(
        self,
        documents: list[CodeDocument],
    ):
        for document in documents:
            dependencies = (
                self._extract_imports(
                    document.content
                )
            )

            self.graph[
                document.file_path
            ] = dependencies

        self._compute_importance_scores()

    def _extract_imports(
        self,
        code: str,
    ):
        dependencies = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    ast.Import,
                ):
                    for alias in node.names:
                        dependencies.append(
                            alias.name
                        )

                elif isinstance(
                    node,
                    ast.ImportFrom,
                ):
                    if node.module:
                        dependencies.append(
                            node.module
                        )

        except Exception:
            pass

        return dependencies

    def _compute_importance_scores(
        self,
    ):
        file_scores = {}

        for (
            file_path,
            dependencies,
        ) in self.graph.items():
            score = len(dependencies)

            file_scores[file_path] = score

        sorted_scores = sorted(
            file_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for rank, (
            file_path,
            score,
        ) in enumerate(sorted_scores):
            normalized_score = max(
                1,
                len(sorted_scores)
                - rank,
            )

            self.importance_scores[
                file_path
            ] = normalized_score

    def get_dependencies(
        self,
        file_path: str,
    ):
        return self.graph.get(
            file_path,
            [],
        )

    def find_related_files(
        self,
        file_path: str,
    ):
        target_dependencies = (
            set(
                self.graph.get(
                    file_path,
                    [],
                )
            )
        )

        related_files = []

        for (
            other_file,
            dependencies,
        ) in self.graph.items():
            if other_file == file_path:
                continue

            overlap = (
                target_dependencies.intersection(
                    dependencies
                )
            )

            if overlap:
                related_files.append(
                    other_file
                )

        return related_files

    def get_importance_score(
        self,
        file_path: str,
    ):
        return self.importance_scores.get(
            file_path,
            1,
        )

    def export_state(
        self,
    ):
        return {
            "graph": self.graph,
            "importance_scores": (
                self.importance_scores
            ),
        }

    def restore_state(
        self,
        state: dict,
    ):
        raw_graph = (
            state.get("graph") or {}
        )

        self.graph = {}

        for (
            file_path,
            dependencies,
        ) in raw_graph.items():
            path_key = str(
                file_path
            )

            if dependencies is None:
                self.graph[path_key] = []

                continue

            self.graph[path_key] = list(
                dependencies
            )

        raw_scores = (
            state.get(
                "importance_scores"
            )
            or {}
        )

        self.importance_scores = {}

        for (
            file_path,
            score,
        ) in raw_scores.items():
            self.importance_scores[
                str(file_path)
            ] = float(
                score
            )