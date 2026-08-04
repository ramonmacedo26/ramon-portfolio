from .config import DATA_DIR, OUTPUTS_DIR


def describe_scaffold() -> dict[str, str]:
    return {
        "data_dir": str(DATA_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
        "status": "scaffold_only",
    }
