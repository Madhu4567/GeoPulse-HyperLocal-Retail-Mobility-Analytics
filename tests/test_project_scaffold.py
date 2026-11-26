from pathlib import Path


def test_expected_project_directories_exist():
    root = Path(__file__).resolve().parents[1]

    for folder in [
        "data",
        "src",
        "sql",
        "dbt",
        "dashboard",
        "airflow",
        "tests",
        "docs",
    ]:
        assert (root / folder).is_dir()