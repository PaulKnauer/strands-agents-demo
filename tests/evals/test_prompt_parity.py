"""Static evals: parity between agent.py (local) and deploy/app.py (cloud).

If these tests fail, the local and cloud agents are running different instructions
or tool schemas — they would behave differently in production.
"""


def test_system_prompt_parity():
    import agent as local_agent
    import deploy.app as cloud_app

    assert local_agent.SYSTEM_PROMPT == cloud_app.SYSTEM_PROMPT, (
        "SYSTEM_PROMPT diverged between agent.py and deploy/app.py.\n"
        f"agent.py:     {local_agent.SYSTEM_PROMPT!r}\n"
        f"deploy/app.py: {cloud_app.SYSTEM_PROMPT!r}"
    )


def test_tools_parity():
    """AC #4 (Story 3.3): TOOLS list in deploy/app.py must name the same tool as agent.py."""
    import deploy.app as cloud_app

    assert len(cloud_app.TOOLS) >= 1, "deploy/app.py TOOLS list is empty"
    tool_name = cloud_app.TOOLS[0]["toolSpec"]["name"]
    assert tool_name == "get_today_date", (
        f"deploy/app.py TOOLS[0] name is '{tool_name}', expected 'get_today_date'.\n"
        "If you rename the tool in agent.py, update deploy/app.py TOOLS list to match."
    )
