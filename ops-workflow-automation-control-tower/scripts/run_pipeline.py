from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print("Ops Workflow Automation Control Tower scaffold")
    print(f"Project root: {root}")
    print("Pipeline implementation pending.")


if __name__ == "__main__":
    main()
