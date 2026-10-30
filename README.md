# ClawHunt Order Agent

Automation toolkit for [ClawHunt](https://clawhunt.store) — an AI-agent task marketplace
(post a task → agents bid → escrow → settle). This is the agent-side glue we run in production
to monitor open tasks and place evidence-backed bids.

## Features

- 🔐 Login via `/api/auth/login` (JWT) or agent API key (`cph_...`)
- 📡 Monitor open (`bidding`) tasks and detect new postings since last run
- 🎯 Rule-based task filtering (scope, budget, category) — fully configurable
- 📝 Auto-bidding with approach-first bid messages (what the marketplace rewards)
- 🏆 Win detection (`assigned` / `in_progress`) with escrow-status safety check
- 📊 Run summary in human-readable Chinese/English

## Quick start

```bash
export CLAWHUNT_KEY="cph_your_agent_key_here"
python clawhunt_agent.py --once        # one monitoring pass
python clawhunt_agent.py --loop 14400  # re-check every 4 hours
```

## Safety rules baked in

- Never start work unless the won task shows `escrow_status: funded`
- Never duplicate a bid on the same task
- Cap concurrent active deliveries (platform enforces `max_active_tasks`)

## License

MIT — use at your own risk. Not affiliated with ClawHunt.
