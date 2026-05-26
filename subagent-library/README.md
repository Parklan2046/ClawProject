# Subagent Library for OpenCode

A curated collection of specialized subagents for OpenCode (ClawProject).

## Usage

```bash
# Install all subagents into your current project
opencode @installer "copy all agents from subagent-library/agents/ into .opencode/agents/"

# Or copy manually
cp subagent-library/agents/*.md .opencode/agents/
```

Then invoke any subagent with `@`:

```
@code-reviewer review auth.py
@security-auditor audit the API endpoints
@python-expert help me type-annotate this module
```

## Agents

| Agent | Category | Mode | What it does |
|-------|----------|------|--------------|
| `@code-reviewer` | Core | `subagent` | Reviews code for bugs, performance, security, maintainability |
| `@security-auditor` | Core | `subagent` | Security vulnerability scanning + CWE references |
| `@docs-writer` | Core | `subagent` | Writes READMEs, API docs, ADRs, changelogs |
| `@debug-agent` | Core | `subagent` | Diagnoses bugs, traces root causes, proposes fixes |
| `@test-writer` | Core | `subagent` | Writes unit/integration/e2e tests |
| `@architect` | Specialty | `subagent` | Software design, feature planning, tradeoff analysis |
| `@python-expert` | Specialty | `subagent` | Python best practices, type hints, async patterns |
| `@git-assistant` | Specialty | `subagent` | Conventional commits, PRs, branch strategy |
| `@refactor-agent` | Specialty | `subagent` | Safely restructures code preserving behavior |
| `@api-designer` | Specialty | `subagent` | REST API design with consistent schemas |
| `@installer` | Meta | `all` | Installs agents into projects (hidden from menu) |

## Installation

### Per-project (recommended)

```bash
Copy-Item -LiteralPath "subagent-library\agents\*.md" -Destination ".opencode\agents\" -Force
```

### Global (available in all projects)

```bash
Copy-Item -LiteralPath "subagent-library\agents\*.md" -Destination "$env:USERPROFILE\.config\opencode\agents\" -Force
```

## Customize

Each `.md` file contains YAML frontmatter — tweak permissions, model, temperature, or prompt to fit your workflow.

## License

Part of ClawProject. Use freely.
