from pathlib import Path
from git import Repo


class RepoCloner:
    def __init__(self, base_path: str = "data/repos"):
        self.base_path = Path(base_path)

    def clone_repository(self, repo_url: str) -> Path:
        repo_name = repo_url.split("/")[-1].replace(".git", "")

        repo_path = self.base_path / repo_name

        if repo_path.exists():
            print(f"Repository already exists: {repo_path}")
            return repo_path

        print(f"Cloning repository: {repo_url}")

        Repo.clone_from(repo_url, repo_path)

        print("Clone completed")

        return repo_path