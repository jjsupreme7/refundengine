# Autonomous Agent System

**Autonomous AI agents working 1am-8am to continuously improve the Refund Engine.**

## Overview

The agent system consists of 3 autonomous teams that run during off-hours (1:00 AM - 8:00 AM Pacific), collaborating via Discord and generating proposals for human review.

### Teams

1. **🏛️ Code Quality Council** (Every 1.5 hours)
   - **Architect**: Reviews architecture and design patterns
   - **Security**: Scans for vulnerabilities and PII exposure
   - **Performance**: Identifies optimization opportunities

2. **📚 Knowledge Curation Team** (Every 15 minutes)
   - **Legal Researcher**: Monitors WA legislature for tax law updates
   - **Taxonomy**: Classifies vendors and products
   - **Summarizer**: Creates plain-English summaries
   - **Cross-Reference**: Links related WAC/RCW/WTD documents

3. **🧠 Pattern Learning Council** (Every 3 hours)
   - **Pattern Discovery**: Finds subtle patterns in corrections
   - **Validator**: Tests patterns against historical data (95% accuracy required)
   - **Edge Case**: Identifies exceptions and boundary conditions

## Architecture

```
agents/
├── core/
│   ├── agent_base.py          # Base agent class
│   ├── approval_queue.py      # Proposal management
│   ├── communication.py       # Discord webhooks
│   ├── daily_digest.py        # Daily email summary
│   └── usage_tracker.py       # Claude Max usage monitoring
├── teams/
│   ├── code_quality_council.py      # Team 1
│   ├── knowledge_curation_team.py   # Team 2
│   └── pattern_learning_council.py  # Team 3
├── workspace/                 # (gitignored)
│   ├── proposals/
│   │   ├── PENDING/
│   │   ├── APPROVED/
│   │   └── REJECTED/
│   ├── discussions/
│   └── usage/
├── config.yaml                # Agent configuration
├── scheduler.py               # APScheduler task runner
└── streamlit_dashboard.py     # Proposal review UI
```

## How It Works

### 1. Agent Workflow

```
1. Agent analyzes codebase/knowledge base
2. Generates findings with Claude API
3. Team discusses findings in multi-agent conversation
4. Creates proposals for human review
5. Posts to Discord for transparency
6. Waits for human approval
```

### 2. Human Approval Process

All changes require explicit human approval:

1. **Review Proposals**: http://localhost:8501
2. **Approve/Reject/Defer**: Each proposal individually
3. **Provide Feedback**: Agents learn from rejections
4. **Track Progress**: Usage statistics and analytics

### 3. Safety Guardrails

- ✅ **Clean Workspace**: All agent work in gitignored `workspace/`
- ✅ **No Direct Changes**: Agents cannot modify codebase directly
- ✅ **Human-in-the-Loop**: All proposals require approval
- ✅ **Isolated Testing**: Agents work in safe sandbox
- ✅ **Usage Monitoring**: Tracks Claude Max API usage (80-85% target)

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set Anthropic API key in .env
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the Dashboard

```bash
streamlit run agents/streamlit_dashboard.py
```

Open http://localhost:8501

### 3. Start the Agent Scheduler

```bash
python agents/scheduler.py
```

Agents will run on schedule (1am-8am).

### 4. Monitor Discord

Agents post to 6 Discord channels:
- `#discussions` - Multi-agent conversations
- `#code-quality` - Code review findings
- `#knowledge` - Tax law research
- `#patterns` - Pattern discoveries
- `#approvals` - New proposals
- `#digest` - Daily summaries

## Configuration

Edit `agents/config.yaml` to customize:

```yaml
schedule:
  start_hour: 1   # 1am
  end_hour: 8     # 8am
  timezone: "America/Los_Angeles"

teams:
  code_quality_council:
    enabled: true
    frequency: "0 */90 1-8 * * *"  # Every 1.5 hours

usage_targets:
  weekly_target_percent: 85  # 85% of Claude Max
  daily_target_messages: 1800  # ~1800/day
```

## Testing

### Test Webhooks

```bash
python test_webhooks.py
```

Should see 6 test messages in Discord.

### Test Daily Digest

```bash
python test_digest.py
```

Sends digest summary to Discord.

### Manual Agent Run

```python
from agents.teams.code_quality_council import run_code_quality_council

result = run_code_quality_council()
print(f"Created {result['proposals_created']} proposals")
```

## Usage Monitoring

The system tracks Claude Max API usage:

- **Target**: 80-85% of weekly limit (~4,000-4,250 messages)
- **Daily Target**: ~1,800 messages (7-hour schedule)
- **Monitoring**: Hourly pace checks during agent hours
- **Alerts**: Discord notifications if below target

View usage in dashboard or check manually:

```python
from agents.core.usage_tracker import UsageTracker

tracker = UsageTracker()
weekly = tracker.get_weekly_usage()

print(f"Usage: {weekly['usage_percent']:.1f}%")
print(f"On pace: {weekly['on_pace']}")
```

## Proposal Workflow

### Proposal States

1. **PENDING**: Awaiting human review
2. **APPROVED**: Human approved, ready to implement
3. **REJECTED**: Human rejected with feedback
4. **DEFERRED**: Postponed for later review

### Reviewing Proposals

In dashboard (http://localhost:8501):

1. Filter by priority/team
2. Read description and impact
3. Choose action:
   - **Approve**: Implement this change
   - **Reject**: Provide feedback (agents learn)
   - **Defer**: Review later

### Proposal Priority

- **🔴 High**: Critical security, major bugs, high-impact improvements
- **🟡 Medium**: Important but not urgent
- **🟢 Low**: Nice-to-have enhancements

## Best Practices

### For Optimal Results

1. **Review Daily**: Check proposals each morning at 8am
2. **Provide Feedback**: Rejection reasons help agents learn
3. **Monitor Usage**: Ensure hitting 80-85% target
4. **Read Discord**: See agent reasoning and discussions
5. **Iterate Configuration**: Adjust frequencies based on proposal quality

### When to Adjust

**Too Many Proposals** (overwhelming):
- Decrease agent frequency
- Increase approval threshold
- Focus on high-priority only

**Too Few Proposals** (underutilized):
- Increase agent frequency
- Enable more teams
- Lower minimum requirements

**Below Usage Target**:
- Extend hours (e.g., 12am-9am)
- Increase frequencies
- Enable all teams

## Troubleshooting

### Agents Not Running

```bash
# Check scheduler logs
python agents/scheduler.py

# Verify config
cat agents/config.yaml

# Test individual team
python -c "from agents.teams.code_quality_council import run_code_quality_council; run_code_quality_council()"
```

### Discord Not Working

```bash
# Test webhooks
python test_webhooks.py

# Check .env
cat .env | grep DISCORD_WEBHOOK
```

### API Rate Limits

If hitting Claude API limits:
- Reduce agent frequency
- Disable low-priority teams temporarily
- Check usage in dashboard

## FAQ

**Q: Do agents modify code directly?**
A: No. Agents only create proposals. Humans approve before any changes.

**Q: What happens if I don't review proposals?**
A: They stay in PENDING. Agents continue working. Review when convenient.

**Q: Can I run agents during the day?**
A: Yes. Edit `config.yaml` schedule. But 1am-8am minimizes disruption.

**Q: How much does this cost?**
A: Uses your existing Claude Max subscription. Target: 80-85% of weekly limit.

**Q: Can agents access production data?**
A: Agents work in isolated workspace. Cannot access live databases or APIs.

**Q: What if an agent makes a mistake?**
A: You review all proposals before implementation. Mistakes caught before deployment.

## Roadmap

- [ ] Email digest delivery (currently Discord-only)
- [ ] Multi-state knowledge base (currently WA only)
- [ ] Auto-deployment of low-risk approved changes
- [ ] Pattern deployment to production refund engine
- [ ] Cross-state pattern learning
- [ ] Vendor classification database

## Support

For issues or questions:
1. Check Discord `#discussions` for agent logs
2. Review `agents/workspace/` for debugging
3. Check usage tracker for API limits
4. See main project documentation

---

**Built with Claude Sonnet 4** | Schedule: 1am-8am Pacific | Target: 80-85% Claude Max Usage
