from part_a_prompt import load_prompt_template, system_prompt


def test_system_prompt_is_the_part_a_rewrite():
    template = load_prompt_template()
    prompt = system_prompt()
    assert "verify_identity" in prompt
    assert "record_promise_to_pay" in prompt
    assert "escalate_to_human" in prompt
    assert "08:00" in prompt and "19:00" in prompt
    assert "consequences" not in template.lower()
    assert "Be persuasive" not in template
    assert "admin mode" in template
    assert "{agent_name}" not in prompt
    assert "2026-08-15" in prompt
    assert "Saturday" in prompt
