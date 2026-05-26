# awesomeOpenCode

111 agents · 15 skills · 5 config presets — the ultimate OpenCode subagent & skill catalog.

Inspired by [weisser-dev/awesome-opencode](https://github.com/weisser-dev/awesome-opencode) and adapted for ClawProject with a new **Manager Toolkit** category.

## Quick Start

Open the catalog:

```
simply open catalog.html in your browser
```

Or install agents into any OpenCode project:

```powershell
# Per-project
Copy-Item -LiteralPath "awesomeOpenCode\agents\*.md" -Destination ".opencode\agents\" -Force

# Global
Copy-Item -LiteralPath "awesomeOpenCode\agents\*.md" -Destination "$env:USERPROFILE\.config\opencode\agents\" -Force
```

## Categories

| Category | Agents | Description |
|----------|:------:|-------------|
| **Core Development** | 8 | API design, backend, frontend, fullstack, GraphQL, microservices, mobile, WebSocket |
| **Language Specialists** | 22 | TypeScript, Python, Go, Rust, Java, C++, C#, Ruby, PHP, Swift, Kotlin, Elixir, Dart, Vue, React, Angular, Next.js, Django, Laravel, Spring, FastAPI, Flutter |
| **Infrastructure** | 13 | Cloud, DevOps, Docker, K8s, Terraform, SRE, networking, security, platform, Azure, DB admin, deployment, incident response |
| **Quality & Security** | 11 | Code review, security audit, penetration testing, compliance, debugger, performance, chaos, accessibility, error detective, architect review, test automator |
| **Data & AI** | 12 | Data engineering, ML, MLOps, NLP, LLM, prompt engineering, SQL, Postgres, DB optimizer, AI engineering, data science, data analyst |
| **Developer Experience** | 11 | Build systems, CLI tools, dependencies, docs, DX, git workflow, legacy code, MCP dev, refactoring, testing, tooling |
| **Specialized Domains** | 8 | Blockchain, embedded, fintech, gaming, IoT, mobile apps, payments, SEO |
| **Business & Product** | 9 | Business analyst, content marketing, legal, product management, project management, sales engineering, scrum master, technical writing, UX research |
| **Manager Toolkit** ⭐ | 3 | Process designer (BPMN), workflow architect (automation), roadmap strategist (RICE/WSJF) |
| **Meta & Orchestration** | 7 | Agent organizer, context manager, error coordinator, knowledge synthesizer, multi-agent coordinator, task distributor, workflow orchestrator |
| **Research & Analysis** | 7 | Competitive analysis, data research, market research, research analyst, scientific literature, search specialist, trend analysis |

## Skills (15)

| Skill | Description |
|-------|-------------|
| `adr-write` | Architecture Decision Records (Nygard template) |
| `api-contract` | OpenAPI/AsyncAPI spec generation |
| `changelog-generate` | CHANGELOG.md from git history |
| `ci-pipeline` | CI/CD config generation |
| `dependency-audit` | CVE scan, license check, unused deps |
| `deploy` | CI/CD pipeline and deployment setup |
| `docker-optimize` | Dockerfile multi-stage, security hardening |
| `env-setup` | Developer environment bootstrap |
| `error-triage` | Stack trace parsing, root cause classification |
| `git-release` | Release notes and semantic version bumps |
| `incident-postmortem` | Blameless postmortem with 5 Whys |
| `migration` | Database/framework migration with rollback |
| `performance-profile` | Performance hotspot analysis |
| `pr-review` | Structured PR review checklist |
| `test-patterns` | Test generation following project conventions |

## Manager Toolkit (New)

Three agents designed for directors, VPs, and team leads:

- **@process-designer** — BPMN process mapping, SIPOC, gap analysis, digital transformation
- **@workflow-architect** — State machines, saga patterns, event-driven automation, cross-system integration
- **@roadmap-strategist** — Now/Next/Later roadmaps, RICE/WSJF prioritization, executive summaries with Gantt charts

## License

MIT. Part of ClawProject.
