from app.ingestion.repo_cloner import RepoCloner
from app.ingestion.file_scanner import FileScanner
from app.ingestion.file_loader import FileLoader


def main():
    repo_url = (
        "https://github.com/tiangolo/fastapi.git"
    )

    cloner = RepoCloner()

    scanner = FileScanner()

    loader = FileLoader()

    repo_path = cloner.clone_repository(
        repo_url
    )

    files = scanner.scan_repository(
        repo_path
    )

    documents = loader.load_files(files)

    sample_document = documents[0]

    print("\nFILE:\n")

    print(sample_document.file_path)

    print("\nDEPENDENCIES:\n")

    for dependency in sample_document.dependencies:
        print(dependency)


if __name__ == "__main__":
    main()