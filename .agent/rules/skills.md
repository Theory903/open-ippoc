# Agent Skills Standard

## What are skills?
Skills are reusable packages of knowledge that extend what the agent can do. Each skill contains:
- Instructions for how to approach a specific type of task
- Best practices and conventions to follow
- Optional scripts and resources the agent can use

## Skill Folder Structure
Skills reside in `.agent/skills/<skill-folder>/`.
Every skill needs a `SKILL.md` file with YAML frontmatter.

```
.agent/skills/
└─── my-skill/
    ├─── SKILL.md       # Main instructions (required)
    ├─── scripts/       # Helper scripts (optional)
    ├─── examples/      # Reference implementations (optional)
    └─── resources/     # Templates and other assets (optional)
```

## SKILL.md Format
The file MUST start with YAML frontmatter:

```markdown
---
name: my-skill
description: Helps with a specific task. Use when you need to do X or Y.
---

# My Skill

Detailed instructions for the agent go here.

## When to use this skill
- Use this when...
- This is helpful for...

## How to use it
Step-by-step guidance, conventions, and patterns the agent should follow.
```

### Frontmatter Fields
- **name** (optional): Unique identifier (lowercase, hyphens). Defaults to folder name.
- **description** (required): Clear description for the agent's context window.

## Best Practices
1.  **Keep skills focused**: Do one thing well.
2.  **Write clear descriptions**: This is how the agent selects the skill.
3.  **Use scripts as black boxes**: Encourage running `script --help` rather than reading code.
4.  **Include decision trees**: Help the agent choose approaches.

## Usage
The agent sees available skills at the start of a conversation. If a skill description matches the current task, the agent reads the full `SKILL.md` and follows it.
