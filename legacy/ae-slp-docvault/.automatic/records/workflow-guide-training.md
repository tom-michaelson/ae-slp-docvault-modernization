# Training Assessment Loop

You have a purposefully broken codebase. Your job is to use AI tools to find as many issues as possible. This workflow helps you iterate: analyze the project, see what you found and missed, get coaching on how to improve your prompts, and try again.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    ONE ITERATION                             │
└─────────────────────────────────────────────────────────────┘

 You analyze a broken project with AI tools
 and write up your findings in a markdown file
                    │
                    ▼
 ┌──────────────────────────────────┐
 │  /automatic.training.log-attempt │  Log what tools and prompts
 │                                  │  you used, plus a self-assessment
 └──────────────────────────────────┘
                    │
                    ▼
 ┌──────────────────────────────────┐
 │  /automatic.training.grade-      │  Score your findings against
 │  assessment                      │  the answer key
 └──────────────────────────────────┘
                    │
                    ▼
 ┌──────────────────────────────────┐
 │  /automatic.training.coach       │  Find out WHY you missed things
 │                                  │  and get better prompts to try
 └──────────────────────────────────┘
                    │
                    ▼
          Refine your approach,
          re-analyze, repeat
```

Each command hands off to the next. Repeat until you're happy with your score.

---

## Step by Step

### 1. Analyze the project

Use whatever AI tools you want to find issues in this codebase. Write your findings into a markdown file. The answer key (`broken-project-*.md` at the repo root) lists issues across three categories: things that are subtly broken at runtime, things that are overengineered, and things that are sloppy.

### 2. Log your attempt

```
/automatic.training.log-attempt my-findings.md
```

This records what tools you used, what prompts you tried, and your honest self-assessment *before* you see your score. Be specific about your prompts — "I asked it to find bugs" is less useful than the actual prompt text. The more detail you provide here, the better the coaching will be.

### 3. Grade your findings

```
/automatic.training.grade-assessment broken-project-clinicflow.md my-findings.md
```

This compares your findings against the answer key. You'll get:

- A **detection rate** (raw and severity-weighted)
- A per-issue breakdown showing what you found, partially found, or missed
- A **depth** assessment: did you identify the root cause, or just the symptom?
- Credit for **additional findings** the answer key didn't list

Partial credit counts as half. Severity weighting means missing a SQL injection hurts your score more than missing a stale TODO comment.

### 4. Get coached

```
/automatic.training.coach tar-0001-clinicflow.md tal-0001-clinicflow.md
```

This is the most valuable step. The coaching report:

- Connects what you missed to the specific prompts you used
- Explains *why* your approach missed each category of issues
- Gives you **specific prompts you can copy-paste** for your next attempt
- If this is iteration 2+, shows what improved and what's still a blind spot

### 5. Iterate

Read the coaching report, refine your approach, re-analyze the project, and run through the loop again. Your second iteration will show progress compared to the first.

---

## Tips

**Use multiple prompt angles.** Don't rely on a single "find all issues" prompt. Make separate passes for bugs, architecture, security, documentation, and configuration.

**Run the app.** Many issues only surface at runtime. Start the application, hit the endpoints, test edge cases. Static code reading alone will miss behavioral bugs.

**Record prompts as you go.** Don't try to remember them after the fact. The coaching step needs your actual prompts to give targeted advice.

**Log your attempt before grading.** The self-assessment is most honest when you haven't seen your score yet.

**Build on what worked.** When you iterate, keep the prompts that found issues and add new ones for the gaps. Don't throw out your whole approach.

**Push past symptoms.** If you find something that seems wrong, ask a follow-up: "Why does this happen? What's the root cause?" Moving from "Symptom only" to "Root cause" turns a partial into a full find.

---

## Common Pitfalls

| Pitfall | What happens | What to do instead |
|---------|-------------|-------------------|
| Bug-only tunnel vision | You find runtime bugs but score 0% on overengineering | Add a dedicated architecture pass: "Trace a request through every layer — which layers add value?" |
| Static analysis only | You miss every issue that requires running the app | Always start the app and test each endpoint before finishing |
| Vague prompts | You get shallow results graded as "Symptom only" | Be specific: "Trace the request from HTTP handler to database" beats "find issues" |
| Ignoring config files | You miss Docker, env var, and documentation problems | Review non-code files: configs, READMEs, Dockerfiles, package manifests |
| Forgetting to log prompts | Coaching can only give generic advice | Write down your prompts during the analysis, not from memory later |

---

## FAQ

**What detection rate should I aim for?**
80% weighted is a strong result. 100% is intentionally hard. Focus on catching all Critical and High severity issues first.

**Can I use different AI tools between iterations?**
Yes, and it's encouraged. Each tool has different strengths. Log what you used so coaching can account for the differences.

**Should I read the answer key before my first attempt?**
No. The point is to develop your ability to discover issues with AI assistance. The coaching loop helps you improve without seeing the answers.

**Can I skip the attempt log?**
You can — grading works standalone. But without it, coaching gives generic advice instead of prompt-specific feedback.

**What if I find issues not in the answer key?**
Good. The answer key isn't exhaustive. Legitimate discoveries are acknowledged in the grading report, not penalized.

**I got Partial on something I thought I fully found — is that fair?**
Partial means you described the symptom but not the root cause. For example, "the health endpoint seems unreliable" is a symptom. "The health endpoint only checks if Express is listening but never verifies the database connection" is the root cause. Next time, ask follow-up prompts to dig deeper.

<!-- AGENT: Insert changelog from .automatic/templates/partials/changelog.md -->
