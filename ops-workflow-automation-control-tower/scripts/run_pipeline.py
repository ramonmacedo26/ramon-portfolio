from pprint import pprint

from ops_workflow_control_tower.pipeline import describe_scaffold


def main() -> None:
    print("Ops Workflow Automation Control Tower")
    pprint(describe_scaffold())


if __name__ == "__main__":
    main()
