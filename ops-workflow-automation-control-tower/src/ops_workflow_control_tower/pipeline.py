from pathlib import Path

from .config import DATA_DIR, OUTPUTS_DIR, RAW_DIR


def describe_scaffold() -> dict[str, str]:
    source_files = sorted(path.name for path in RAW_DIR.glob("*.csv"))
    return {
        "data_dir": str(DATA_DIR),
        "raw_dir": str(RAW_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
        "source_file_count": str(len(source_files)),
        "source_files": ", ".join(source_files),
        "status": "synthetic_inputs_ready",
    }
