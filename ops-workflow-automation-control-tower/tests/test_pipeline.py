from ops_workflow_control_tower.pipeline import describe_scaffold


def test_scaffold_description() -> None:
    description = describe_scaffold()
    assert description["status"] == "synthetic_inputs_ready"
    assert description["source_file_count"] == "3"
