from eval import run


def test_all_scripted_scenarios_pass():
    assert run() == 0
