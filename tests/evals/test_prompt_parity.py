"""Static eval: SYSTEM_PROMPT must be identical in agent.py and deploy/app.py.

If this test fails, local and cloud agents are running different instructions.
"""

def test_system_prompt_parity():
    import agent as local_agent
    import deploy.app as cloud_app

    assert local_agent.SYSTEM_PROMPT == cloud_app.SYSTEM_PROMPT, (
        "SYSTEM_PROMPT diverged between agent.py and deploy/app.py.\n"
        f"agent.py:     {local_agent.SYSTEM_PROMPT!r}\n"
        f"deploy/app.py: {cloud_app.SYSTEM_PROMPT!r}"
    )
