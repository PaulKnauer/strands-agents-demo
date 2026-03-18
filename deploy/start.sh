#!/bin/bash
# Install third-party dependencies before starting the app.
# strands-agents and python-dotenv are not pre-installed in the AgentCore runtime.
pip install -q -r requirements.txt && python app.py
