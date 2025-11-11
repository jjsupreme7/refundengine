# Claude Code Workflows & Best Practices

This document contains helpful workflows and prompts for working effectively with Claude Code.

## 7 Core Development Rules

When working on new features or significant changes, follow this workflow:

1. **Think & Plan First**: Read through the codebase for relevant files, understand the problem, and write a plan to `tasks/todo.md`

2. **Create Actionable Todo List**: The plan should have a list of specific todo items that can be checked off as completed

3. **Get Approval**: Before beginning work, check in and verify the plan is correct

4. **Execute Incrementally**: Work through todo items one by one, marking them complete as you go

5. **High-Level Communication**: At every step, provide high-level explanations of changes made (not overwhelming detail unless requested)

6. **Simplicity First**: Make every task and code change as simple as possible. Avoid massive or complex changes. Each change should impact as little code as possible. Everything is about simplicity.

7. **Review & Document**: Add a review section to `todo.md` with a summary of changes made and any other relevant information

## Security Review Prompt

After completing code changes, use this prompt:

```
Please check through all the code you just wrote and make sure it follows security best practices.
Make sure there are no sensitive information in the frontend and there are no vulnerabilities that
can be exploited.
```

**Common Security Checks:**
- No API keys, passwords, or secrets in code
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS prevention
- CSRF protection where applicable
- Authentication and authorization checks
- Rate limiting for APIs
- Secure file upload handling
- Environment variables for sensitive config

## Learning & Knowledge Transfer Prompt

When you want to understand changes in depth, use this prompt:

```
Please explain the functionality and code you just built out in detail. Walk me through what you
changed and how it works. Act like you're a senior engineer teaching me code.
```

**Good for:**
- Understanding new patterns or architectures
- Learning unfamiliar libraries or frameworks
- Building mental models of complex systems
- Preparing to explain changes to team members

## Productive Work Sessions

Instead of doom scrolling during AI processing time, use these prompts to stay productive:

### Idea Generation & Brainstorming
```
I have [TIME] minutes while you're working. Let's brainstorm ideas for [TOPIC/FEATURE/PROBLEM].
Help me think through creative solutions or new angles.
```

### Business Strategy
```
While you're processing, I want to think about [BUSINESS ASPECT: marketing/pricing/growth/etc].
Can you ask me strategic questions to help clarify my thinking?
```

### Content Planning
```
I'm working on content about [TOPIC]. While you're coding, help me outline a blog post/video/tweet
thread that would provide value to my audience.
```

### Reflection & Planning
```
Let's do a quick reflection session. Ask me 3-5 questions about [PROJECT/GOAL] to help me think
through what's working and what needs adjustment.
```

### Learning Session
```
Teach me about [TECHNOLOGY/CONCEPT] in bite-sized chunks while you're working on the code.
Give me one concept at a time so I can learn during the wait.
```

### Problem Solving
```
I'm stuck on [PROBLEM]. Let's use this time to think through it together. Ask me clarifying
questions and help me break it down.
```

## Example Workflow for New Feature

```markdown
User: "I need to add user authentication to the app"

Claude: [Reads codebase] I'll create a plan in tasks/todo.md:

**TODO: User Authentication**
- [ ] Set up authentication database tables (users, sessions)
- [ ] Create password hashing utilities
- [ ] Build registration endpoint
- [ ] Build login endpoint
- [ ] Add session middleware
- [ ] Create protected route decorator
- [ ] Add logout endpoint
- [ ] Update frontend with login form
- [ ] Test authentication flow

Does this plan look good?

User: "Yes, proceed"

Claude: Starting on todo 1... [works]
Claude: Completed todo 1 - Added users table with id, email, password_hash, created_at
Claude: Starting on todo 2... [works]
[continues...]

User: [Uses productive time prompt] "While you're working, help me think through my
marketing strategy for this app"

Claude: [Asks strategic questions during processing time]

[After completion]

User: "Please explain the authentication code you built like you're a senior engineer"

Claude: [Provides detailed technical explanation]

User: "Now do a security review"

Claude: [Performs security audit]
```

## Tips for Effective Collaboration

1. **Be Specific**: Instead of "make it better", say "reduce the number of database queries in the user profile page"

2. **Provide Context**: Share what you've tried, what didn't work, and what constraints you have

3. **Iterate in Small Steps**: It's better to make 5 small changes with verification than 1 massive change

4. **Ask for Explanations**: Don't hesitate to ask "why" or "how does this work" - understanding is key

5. **Use the Productive Time**: Transform waiting time into learning, planning, or creative thinking time

6. **Review Before Moving On**: Always review changes before adding more complexity on top

## Project-Specific Notes

### RefundEngine Tax Scraper
- Uses PDF-based approach for Washington State RCW laws
- Database schema supports vector embeddings for RAG system
- Rate limited to 1 second between requests
- All scrapers follow same pattern: discover → download → extract → store
