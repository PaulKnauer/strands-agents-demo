# strands-agents-demo

A demonstration project for building AI agents using the [Strands Agents SDK](https://strandsagents.com), scaffolded and orchestrated with the [BMAD Framework](https://github.com/bmad-agents/bmad-method) (Built-in Multi-Agent Design).

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [BMAD Agent Team](#bmad-agent-team)
- [Getting Started](#getting-started)
- [Workflows](#workflows)
- [Contributing](#contributing)

## Overview

This project combines two agent frameworks:

- **Strands Agents SDK** — AWS's Python framework for building production-ready AI agents with tools, memory, and multi-agent orchestration.
- **BMAD Framework (v6.2.0)** — A structured multi-agent development methodology that guides projects through analysis, planning, solutioning, and implementation phases using specialized AI agents.

The BMAD agents guide and accelerate the development of Strands-based agent applications through defined roles, workflows, and artifacts.

## Project Structure

```text
strands-agents-demo/
├── _bmad/                    # BMAD framework core (source of truth)
│   ├── _config/              # Agent, skill, workflow, and tool manifests
│   ├── _memory/              # Persistent agent memory and documentation standards
│   ├── core/                 # Built-in skills: brainstorming, research, editing
│   ├── bmm/                  # Agent Management Module: agents and workflows
│   ├── bmb/                  # Builder Module: agent and workflow builders
│   └── tea/                  # Test Architecture Enterprise: QA and testing
├── _bmad-output/             # Generated project artifacts
│   ├── planning-artifacts/   # PRDs, architecture docs, UX specs
│   ├── implementation-artifacts/ # Code, stories, implementation notes
│   └── test-artifacts/       # Test plans and results
├── .claude/skills/           # Claude Code IDE skill integrations (synced from _bmad)
├── .cursor/skills/           # Cursor IDE skill integrations (synced from _bmad)
├── .agents/skills/           # Generic agent skill integrations (synced from _bmad)
├── docs/                     # Project documentation
└── README.md
```

## BMAD Agent Team

The following specialized agents are available to guide development:

| Agent | Name | Role |
|-------|------|------|
| 📊 analyst | Mary | Business analysis, market research, requirements elicitation |
| 🏗️ architect | Winston | System architecture, cloud infrastructure, API design |
| 💻 dev | Amelia | Story execution, TDD, code implementation |
| 📋 pm | John | PRD creation, requirements discovery, stakeholder alignment |
| 🧪 qa | Quinn | Test automation, API testing, E2E testing |
| 🚀 quick-flow-solo-dev | Barry | Rapid spec creation and lean implementation |
| 🏃 sm | Bob | Sprint planning, story preparation, agile ceremonies |
| 📚 tech-writer | Paige | Technical documentation and knowledge curation |
| 🎨 ux-designer | Sally | User research, interaction design, UI patterns |
| 🧪 tea | Murat | Master test architect, risk-based testing, CI/CD governance |

## Getting Started

### Prerequisites

- Claude Code CLI or Cursor IDE
- BMAD Framework v6.2.0 (included)

### Running Agents

Invoke any BMAD agent directly using slash commands in your IDE:

```text
/bmad-pm          # Start a product management session
/bmad-architect   # Engage the architect
/bmad-dev         # Start a development session
/bmad-party-mode  # Start a collaborative multi-agent discussion
```

### Development Workflow

BMAD organizes work into four phases:

1. **Analysis** — Run `/bmad-analyst` or `/bmad-domain-research` to investigate the problem space.
2. **Planning** — Run `/bmad-create-prd` to define requirements, then `/bmad-create-architecture` for technical design.
3. **Solutioning** — Run `/bmad-create-epics-and-stories` to break work into executable stories.
4. **Implementation** — Run `/bmad-dev-story` to implement each story with tests.

Artifacts from each phase are saved to `_bmad-output/`.

## Workflows

Key workflows available via slash commands:

| Command | Description |
|---------|-------------|
| `/bmad-create-prd` | Create a Product Requirements Document |
| `/bmad-create-architecture` | Design the technical solution |
| `/bmad-create-epics-and-stories` | Break requirements into epics and stories |
| `/bmad-sprint-planning` | Plan sprint execution |
| `/bmad-dev-story` | Implement a story |
| `/bmad-code-review` | Adversarial code review |
| `/bmad-quick-spec` | Rapid tech spec for small changes |
| `/bmad-party-mode` | Multi-agent collaborative session |

## Contributing

This project follows the BMAD methodology. Before contributing:

1. Review the agent manifest at `_bmad/_config/agent-manifest.csv`.
2. Check documentation standards at `_bmad/_memory/tech-writer-sidecar/documentation-standards.md`.
3. Use `/bmad-create-story` to create a story before implementing changes.
4. Run `/bmad-code-review` before submitting.
