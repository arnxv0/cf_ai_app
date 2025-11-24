# Quick Start: Your Tadata Setup (Notion, Supabase, Exa)

## What You Have

You've connected these services in Tadata:

- **Notion** - Documentation and knowledge management
- **Supabase** - Database and backend services
- **Exa** - AI-powered semantic search

## How to Use Tadata (No API Key Needed!)

### Step 1: Your Services Are Already Connected

Since you connected Notion, Supabase, and Exa at [app.tadata.com/connectors](https://app.tadata.com/connectors), they're ready to use via OAuth.

### Step 2: Track in Pointer

In Pointer Settings → Tadata Integration:

1. Check the boxes for: ☑️ Notion, ☑️ Supabase, ☑️ Exa
2. This saves your preferences locally (tracking only)

### Step 3: Test Your Tools

Go to [app.tadata.com/playground](https://app.tadata.com/playground) and try:

**Notion:**

```
Search my Notion for "project roadmap"
Create a page titled "Meeting Notes"
```

**Supabase:**

```
Query users table in my Supabase database
Get row count from products table
```

**Exa:**

```
Search for "latest AI research papers"
Find articles about "vector databases"
```

### Step 4: Connect to MCP Clients

Tadata uses **MCP (Model Context Protocol)**. Connect to:

- **Claude Desktop** - Add Tadata MCP server in settings
- **Cursor** - Configure MCP connection
- **Custom agents** - Use MCP client library

See: [Tadata MCP docs](https://docs.tadata.com/getting-started/key-concepts)

## Why No API Key?

Tadata authentication works like this:

1. **OAuth for services** - You authorized Notion/Supabase/Exa with OAuth
2. **MCP for agents** - Your AI agent connects via MCP protocol
3. **Tadata handles the rest** - Credentials stored securely, tokens auto-refreshed

## Quick Examples

### Notion + Exa Research Workflow

```
"Search Exa for 'machine learning papers' and save summaries to my Notion workspace"
```

### Supabase Data Query

```
"Query my Supabase database for users who signed up this week"
```

### Knowledge Management

```
"Find my Notion page about 'database architecture' and update it with latest info from Exa"
```

## Troubleshooting

**Can't find your tools?**

- Go to [app.tadata.com/connectors](https://app.tadata.com/connectors)
- Verify Notion, Supabase, and Exa show "Connected" status
- Click "Reconnect" if any show expired

**OAuth expired?**

- Re-authorize at app.tadata.com
- Tadata auto-refreshes tokens but OAuth can expire if unused for 90+ days

**Need more connectors?**

- Click "Add Connector" in Tadata dashboard
- Popular additions: Linear (issues), GitHub (code), Slack (notifications)

## Resources

- **Your Dashboard**: [app.tadata.com](https://app.tadata.com)
- **Test Tools**: [app.tadata.com/playground](https://app.tadata.com/playground)
- **Docs**: [docs.tadata.com](https://docs.tadata.com)
- **Support**: [support@tadata.com](mailto:support@tadata.com)
