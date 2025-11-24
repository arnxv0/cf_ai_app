# Tadata Integration Guide

## Overview

Tadata provides 100+ pre-built, optimized connectors for AI agents with managed authentication and token-efficient responses. This integration allows Pointer to track and configure your Tadata connectors directly from the settings panel.

> **Note**: Tadata uses MCP (Model Context Protocol) servers. Tools are accessed through your Tadata dashboard at [app.tadata.com](https://app.tadata.com), and this integration helps you track which connectors you've enabled.

## Setup

### 1. Connect Services in Tadata Dashboard

1. Visit [https://app.tadata.com/connectors](https://app.tadata.com/connectors)
2. Sign up or log in
3. Click "Connect" on services you want (Notion, Supabase, Exa, etc.)
4. Complete OAuth authorization for each service

> **No API key needed!** Tadata uses OAuth and MCP servers.

### 2. Track in Pointer

1. Open Pointer Settings
2. Go to **Tadata Integration** panel
3. Check the boxes for services you've connected in Tadata
4. These are saved locally for tracking purposes only

### 3. Access Your Tools

- Test tools in [Tadata Playground](https://app.tadata.com/playground)
- Connect to Claude Desktop, Cursor, or other MCP clients
- See [Tadata MCP documentation](https://docs.tadata.com) for integration details
- **Notion** - Documentation and knowledge base
- **Jira** - Project management
- **Sentry** - Error tracking and monitoring
- **Render** - Deployment platform
- **Supabase** - Database and backend services

## Usage

Once configured, Tadata tools are automatically available to your AI agent. Simply use natural language:

### Examples

**Linear Integration:**

```
"Create a Linear issue: Bug in authentication flow"
"What are my open Linear issues?"
"Assign this ticket to Sarah"
```

**GitHub Integration:**

```
"What are the open PRs in my repo?"
"Create a GitHub issue for this bug"
"Show me recent commits"
```

**Slack Integration:**

```
"Send a Slack message to #engineering"
"What are the latest messages in #general?"
"Post this update to Slack"
```

**Notion Integration:**

```
"Add this to my Notion workspace"
"Search Notion for meeting notes"
"Create a new page in my docs"
```

## Architecture

### Backend Integration

The Tadata integration lives in `src-python/tools/tadata.py`:

```python
from tools.tadata import get_tadata_integration

# Get configured tools
tadata = get_tadata_integration()
if tadata.is_configured():
    tools = tadata.get_tools()
```

Tools are automatically added to the Coordinator agent when:

1. `TADATA_API_KEY` is set in environment
2. At least one connector is enabled in `TADATA_CONNECTORS`

### Settings Storage

- **API Key**: Stored encrypted in `settings.db` under `TADATA_API_KEY`
- **Enabled Connectors**: JSON array in `TADATA_CONNECTORS`
  - Example: `["linear", "github", "slack"]`

### Hot Reload

When you save Tadata settings in the UI, the integration automatically reloads without restarting the backend:

```python
# routes/settings.py
if request.key in ["TADATA_API_KEY", "TADATA_CONNECTORS"]:
    reload_tadata_integration()
```

## Available Connectors

| Connector | Description        | Use Cases                                   |
| --------- | ------------------ | ------------------------------------------- |
| Linear    | Issue tracking     | Create/read/update issues, manage sprints   |
| GitHub    | Code repository    | PRs, issues, commits, releases              |
| Slack     | Team chat          | Send messages, read channels, post updates  |
| Notion    | Documentation      | Create pages, search docs, manage workspace |
| Jira      | Project management | Tickets, sprints, projects                  |
| Sentry    | Error tracking     | View errors, create issues, monitor health  |
| Render    | Deployment         | Deploy apps, check status, manage services  |
| Supabase  | Backend/DB         | Query database, manage auth, storage        |

## Advanced Configuration

### Custom API Endpoints

If you have a self-hosted Tadata instance, set the base URL:

```python
# In src-python/tools/tadata.py
self.client = TadataClient(
    api_key=self.api_key,
    base_url="https://your-tadata-instance.com"
)
```

### Rate Limiting

Tadata handles rate limiting automatically. If you hit limits:

1. Check your plan at [https://www.tadata.com/pricing](https://www.tadata.com/pricing)
2. Monitor usage in Tadata dashboard
3. Consider upgrading for higher limits

### OAuth Connectors

Some connectors (GitHub, Slack, etc.) require OAuth:

1. Click "Connect" in Tadata dashboard for the connector
2. Authorize the OAuth app
3. Credentials are securely managed by Tadata
4. No tokens stored in Pointer

## Troubleshooting

### Tools Not Showing Up

**Check logs:**

```bash
# Look for Tadata initialization messages
tail -f logs/backend.log | grep -i tadata
```

**Common issues:**

- API key not saved correctly
- No connectors enabled
- `tadata-py` package not installed

### Authentication Errors

**OAuth connectors:**

1. Go to [https://app.tadata.com/connectors](https://app.tadata.com/connectors)
2. Click "Reconnect" on the failing connector
3. Re-authorize OAuth permissions

**API key issues:**

- Verify key is valid in Tadata dashboard
- Check for typos when pasting
- Ensure key has proper permissions

### Installation

Tadata connectors are accessed via MCP servers. Configuration is stored in Pointer settings for reference:

```bash
# No additional installation needed
# Tadata runs as an MCP server through their platform
```

## Security

- API keys are encrypted at rest in `settings.db`
- OAuth tokens managed by Tadata (not stored locally)
- All API calls use HTTPS
- Credentials never logged or exposed

## Resources

- **Tadata Documentation**: [https://docs.tadata.com](https://docs.tadata.com)
- **Connector Catalog**: [https://app.tadata.com/connectors](https://app.tadata.com/connectors)
- **GitHub Examples**: [https://github.com/tadata-org/fastapi_mcp](https://github.com/tadata-org/fastapi_mcp)
- **Support**: [support@tadata.com](mailto:support@tadata.com)

## Example Workflows

### Bug Triage Agent

Enable: Sentry + GitHub + Slack + Render

```
"Check Sentry for new errors"
"Create GitHub issues for critical errors"
"Post deployment status to #alerts"
```

### Customer Support

Enable: Linear + Slack + Notion + Intercom

```
"What are open support tickets?"
"Add this to our help docs in Notion"
"Send update to customer via Slack"
```

### DevOps Automation

Enable: GitHub + Render + Sentry + PagerDuty

```
"Deploy latest main branch to production"
"Check error rate after deployment"
"Create incident if errors spike"
```
