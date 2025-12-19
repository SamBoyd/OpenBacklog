# Setting Up MCP with OpenBacklog

OpenBacklog integrates with AI tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). This allows you to use your existing AI subscriptions (Claude Pro, Cursor, etc.) to interact with your tasks and planning data.

## Supported Tools

- **Claude Code** (CLI) - Full support
- **Claude Desktop** - Full support
- **Cursor** - Coming soon

## Claude Code Setup

### 1. Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

See the [official Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for detailed installation instructions.

### 2. Configure MCP Server

Add OpenBacklog to your MCP configuration. Create or edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openbacklog": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Or use the `--mcp` flag when starting Claude Code:

```bash
claude --mcp http://localhost:8000/mcp
```

### 3. Authenticate

When Claude Code connects to OpenBacklog, you'll be prompted to authenticate via your browser.

## Available Tools

Once connected, Claude Code can help you with:

**Task Management**
- View, create, update tasks
- Manage checklists
- Track task status

**Initiative Management**
- Create and organize initiatives
- Link tasks to initiatives

**Strategic Planning**
- Define product vision
- Create strategic pillars and outcomes
- Manage roadmap themes

**Narrative Tools**
- Define heroes (user personas)
- Identify villains (problems to solve)
- Track conflicts between heroes and villains

## Example Prompts

```
"Show me my current tasks"
"Create a new initiative for user authentication"
"What's my product vision?"
"Help me break down this feature into tasks"
"What conflicts are we trying to resolve?"
```

## Troubleshooting

**Connection refused**: Ensure OpenBacklog is running (`docker-compose up`)

**Authentication failed**: Clear your browser cookies for localhost and try again

**Tools not appearing**: Restart Claude Code after updating MCP configuration
