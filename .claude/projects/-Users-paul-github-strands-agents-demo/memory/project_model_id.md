---
name: Active Bedrock model ID
description: The working Bedrock model ID for this project — claude-3-sonnet is broken, use claude-3-haiku
type: project
---

MODEL_ID changed from `anthropic.claude-3-sonnet-20240229-v1:0` (requires AWS Marketplace subscription — broken on this account) to `anthropic.claude-3-haiku-20240307-v1:0` (confirmed working 2026-03-18).

**Why:** claude-3-sonnet requires a Marketplace subscription not active on Paul's account.
**How to apply:** Use `anthropic.claude-3-haiku-20240307-v1:0` as the default when suggesting model IDs for this project.
