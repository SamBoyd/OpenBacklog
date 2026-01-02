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

OpenBacklog provides two MCP server modes:

**Execution Mode** (5 tools) - Minimal toolset for coding workflows:
- Query and update initiatives
- Query and update tasks
- Get strategic context summary

**Planning Mode** (35+ tools) - Full toolset for strategic planning:
- All execution tools
- Framework tools for vision, pillars, outcomes, themes
- Hero, villain, and conflict management
- Roadmap prioritization

#### Why Two Servers?

LLMs have a fixed context window, and every MCP tool definition consumes tokens whether the tool is used or not. When you're focused on **implementation** (pulling down a task and coding), you don't need 35+ strategic planning tools consuming your context window.

**The Problem:**
- Tool definitions take up valuable context space
- More tools = less room for code, conversation, and reasoning
- When coding, you rarely need framework tools, hero/villain management, or roadmap prioritization

**The Solution:**
- **Execution server**: Only 5 essential tools (~85% reduction)
- **Strategy server**: Full 35+ toolset for when you're planning
- Use the right server for the right job

**Benefits:**
- More context available for actual code when implementing
- Faster AI tool selection with fewer options to consider
- Clear mental model: "I'm coding" vs "I'm planning"
- Better performance and lower API costs

#### Recommended: Dual-Server Configuration

For best performance, configure both servers. Use the execution server when coding, and the strategy server when planning:

```json
{
  "mcpServers": {
    "openbacklog-execution": {
      "url": "http://localhost:8000/mcp/execution/",
      "description": "Minimal toolset for coding workflows"
    },
    "openbacklog-strategy": {
      "url": "http://localhost:8000/mcp/planning/",
      "description": "Full toolset for strategic planning"
    }
  }
}
```


```bash
claude --mcp http://localhost:8000/mcp/planning/
```

### 3. Authenticate

When Claude Code connects to OpenBacklog, you'll be prompted to authenticate via your browser.

### 4. Managing MCP Servers

Once configured, you can dynamically enable and disable MCP servers during your Claude Code session using the `/mcp` command:

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
