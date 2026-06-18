# Triage SharePoint Comments

Analyze SME review comments from `sharepoint-comments.json` and classify each as useful or not useful for the develop workflow. This does NOT regenerate the functional spec — it produces overlay files that the context system feeds into planning and implementation.

## Usage
/triage-comments entry_point_folder_path: <path>

## Parameters
- **entry_point_folder_path** (required): Path to the entry point folder (e.g., `docs/entry-points/api-endpoints/1055-spring-helpfileservice-gethelpfiles`)

## Prerequisite Check

1. Verify `{entry_point_folder_path}/sharepoint-comments.json` exists — if not, report "No comments to triage" and stop
2. Read `{entry_point_folder_path}/functional-spec.md` — needed for context but not a hard blocker. If missing, warn and proceed (comments can still be classified based on their own content)

## Process

### Step 1: Load Inputs

Read the following files from the entry point folder:
- `sharepoint-comments.json` — the raw comments to classify
- `functional-spec.md` — to understand what each highlighted section means in context

### Step 2: Classify Each Comment

For each comment in `sharepoint-comments.json`, determine whether it is **USEFUL** or **NOT_USEFUL** based on the classification criteria below.

#### The Core Test: Does This Change Requirements?

Before classifying, ask: **"Does this comment change, add, or constrain what we need to build?"** If the answer is no — if the spec already describes the behavior correctly and the comment just confirms it — the comment is NOT useful. The develop workflow only needs comments that alter implementation decisions.

#### USEFUL — Comment should be kept

A comment is useful ONLY if it does one of the following:

| Criterion | Example |
|-----------|---------|
| **Provides a concrete answer that adds NEW information** | "Sent by batch job and preset trigger" — the spec didn't know the mechanism |
| **Corrects factual errors in the spec** | "Incorrect. Should be Loc Purp Desc" — fixes a wrong column name |
| **Adds domain knowledge NOT already in the spec** | "Customers in Contact Manager with business user function 'Imbalance Penalty Notice'" — spec didn't know the source |
| **Changes or constrains behavior beyond what spec describes** | "This needs to remain read-only" — when spec proposed editability |
| **Resolves a question where the spec proposed alternatives and the answer picks one** | "Leave as is, all help files are open to all" — spec asked about role-based vs open access, and this picks open access with a reason |
| **Corrects terminology or naming** | "JP means Jackson Prairie, not Joint Participant" — spec had it wrong |
| **Provides specific values, thresholds, or business rules** | "The threshold is 101 Dth" — a concrete value the spec didn't have |

#### NOT_USEFUL — Comment can be ignored

A comment is NOT useful if it matches ANY of these:

| Criterion | Example |
|-----------|---------|
| **Internal routing / delegation** | "@Lofthouse, Tracy - not sure if the dependencies are IT" |
| **Tagging people without substance** | "IT specific, FYI @Kilpack, Jeramie and @Lofthouse, Tracy" |
| **Pure acknowledgment with no decision** | "Looks good" on a descriptive paragraph that wasn't a question |
| **Process/meta comments** | "We'll discuss this in the next meeting" |
| **Unresolved / uncertain responses** | "Not sure", "Probably before save", "I think so" — hedged language without a firm decision is not a decision |
| **"Keep as is" / "Keep current state" when the spec already describes that behavior** | Q: "What are the validation rules?" A: "Keep as current state" — this doesn't tell us what the rules ARE, it just says don't change them. If the spec already describes the current behavior, this adds nothing. |
| **Confirms what the spec already says without adding information** | Q: "How often do partial save failures occur?" A: "Rarely" — this doesn't change any requirements. The spec already handles the save-all flow. |
| **Describes something as "informational" without answering the actual questions** | Q: "What happens if both On and Off are Yes? What validation is needed?" A: "It's just informational to the world" — doesn't answer the specific validation questions asked |
| **Dodges the specific sub-questions** | Q has 4 numbered sub-questions. A says "Keep as current state" without addressing any of them. The actual questions remain unanswered. |

**Key principle on "Leave as is" / "Keep existing functionality":**
These are ONLY useful when they come with **additional information that the spec doesn't already have**. Examples:
- USEFUL: "Leave as is, all help files are open to all" — the "open to all" part is new info that resolves the permission model question
- USEFUL: "Keep existing functionality. Based on general release timeframes." — the rationale ("general release timeframes") is new info
- NOT USEFUL: "Keep as current state" with no elaboration when the spec already describes current behavior
- NOT USEFUL: "This is just informational. Keep as current state." — doesn't answer the specific questions about validation rules or data relationships

### Step 3: Group Comments on the Same Topic

When multiple reviewers comment on the **same highlighted text** (same question), group them together in the output. All responses to a question should appear under a single heading. This is common — e.g., both KJ and LT may answer Q3.

### Step 4: Write Output Files

Write **two** markdown files to the entry point folder.

#### File 1: `{entry_point_folder_path}/useful-comments.md`

```markdown
# Client Review Decisions

> SME decisions from spec review. These resolve open questions and correct errors
> in the functional specification. Treat as authoritative — where these conflict
> with the spec, these take precedence.

## [Short topic description from highlighted text]

- **Question/Section:** [The highlighted text, condensed to key question]
- **Decision:** [The answer text from the comment]
- **Author:** [Author name] ([date in YYYY-MM-DD])
- **Impact:** [1-2 sentence synthesis of what this means for implementation. Be specific — e.g., "No role-based filtering needed" not "Keep as is"]

[If multiple reviewers answered the same question, list each response:]
- **Additional response:** [Author] — [answer text]

---

[Repeat for each useful comment/group]
```

#### File 2: `{entry_point_folder_path}/not-useful-comments.md`

```markdown
# Client Review Comments — Excluded

> These comments were reviewed and determined to not contain actionable decisions
> or corrections for the functional specification.

## [Short topic]

- **Author:** [Author name] ([date])
- **Comment:** [The comment text]
- **Highlighted:** [What was highlighted]
- **Reason:** [Why this was excluded — e.g., "Internal routing between reviewers, no decision made"]

---

[Repeat for each not-useful comment]
```

### Step 5: Summary

Output a summary to the console:

```
Triaged comments for: {entry_point_folder_path}
  Source: sharepoint-comments.json ({N} total comments)

  Useful:     {X} comments → useful-comments.md
  Not useful: {Y} comments → not-useful-comments.md

  Topics resolved:
    - [Topic 1]: [brief decision]
    - [Topic 2]: [brief decision]
    ...
```

## Edge Cases

**All comments are useful:** Write `not-useful-comments.md` with a note that all comments contained actionable information.

**All comments are not useful:** Write `useful-comments.md` with a note that no actionable decisions were found in the review comments.

**Empty comments array:** Report "No comments found in sharepoint-comments.json" and write neither file.

**Comment references text not found in spec:** Still classify it — the comment itself may be self-explanatory. Note in the Impact that the referenced section was not found in the current spec.

## Success Criteria

- [ ] All comments from `sharepoint-comments.json` are classified
- [ ] `useful-comments.md` written with Impact lines that synthesize decisions
- [ ] `not-useful-comments.md` written with exclusion reasons
- [ ] Comments on the same topic are grouped together
- [ ] Console summary shows topic decisions
- [ ] No comments are lost (useful + not-useful = total)
