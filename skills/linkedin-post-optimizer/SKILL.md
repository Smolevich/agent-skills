---
name: linkedin-post-optimizer
description: >
  Transform raw ideas into authentic LinkedIn posts adapted to the user's profile
  level, voice, and audience. Use this skill whenever the user mentions LinkedIn,
  wants to write a post, draft content for social media, optimize engagement,
  improve their professional presence, or asks about content strategy — even if
  they don't explicitly say "LinkedIn post". Includes AI slop detection and
  engagement optimization.
allowed-tools: Read, Glob, Grep, Write, AskUserQuestion
argument-hint: drafts/my-idea.md
user-invocable: true
---

# LinkedIn Post Optimizer

Transform raw ideas into LinkedIn posts that preserve the user's authentic voice — not generic AI-sounding content.

Core goals:
1. Capture the person's actual voice and style
2. Structure the idea clearly (hook -> body -> conclusion)
3. Remove friction that would stop readers
4. Never produce text that sounds machine-generated

For voice guidelines, AI slop detection rules, and anti-patterns, read `references/voice-guidelines.md`.
For draft/output examples, read `references/examples.md`.

## Step 1: Get the Idea

If `$ARGUMENTS` is provided, read the file at that path as the raw idea.

If `$ARGUMENTS` is empty or the file is missing, ask directly:

> "What's the idea for your LinkedIn post? Share it in any form — messy notes, bullet points, a sentence, anything."

Wait for the idea before proceeding.

## Step 2: Gather LinkedIn Stats

Ask the following using AskUserQuestion (all questions in one message):

1. **Audience Size** — connections + followers count
   - Options: "Under 500", "500-1500", "1500-5000", "5000+"

2. **Post History** — posts published in the last 3 months
   - Options: "0-2 posts", "3-10 posts", "10+ posts"

3. **Typical Engagement** — average impressions per post
   - Options: "Under 500", "500-1500", "1500-5000", "5000+"

4. **Preferred Tone**
   - Options: "Formal/professional", "Casual/conversational", "Technical/detailed", "Mixed"

5. **Language** — post language
   - Options: "Russian (RU)", "English (EN)", "Other"

6. **Network Language** — primary language of the LinkedIn network
   - Options: "Mostly Russian", "Mostly English", "Mixed / international"

Wait for answers. These determine length, structure, boldness of claims, and realistic reach expectations.

### Language x Audience Alignment

**Same language (RU->RU or EN->EN):** Proceed normally.

**Mismatch (e.g. writing EN, network is mostly RU):**

LinkedIn does not route posts by language — the algorithm distributes based on engagement signals. A mismatch means the existing network sees a foreign-language post, doesn't engage, weak "golden hour" signal follows, and the algorithm limits distribution before the target audience ever sees it.

Warn the user and suggest a transition strategy:
1. **Parallel posting** — same idea in both languages as separate posts
2. **Gradual shift** — one post per month in the new language while building connections
3. **Network-first** — build target-language connections before switching

Generate the post in the requested language, but set realistic expectations.

**Hook style by language:**
- **EN LinkedIn:** personal story + specific data point performs best
- **RU LinkedIn:** contrarian statement or practical numbered list performs best

## Step 3: Check Profile Context

Read `profile-context.md` in the skill directory (or in the project root) if it exists. This file contains additional context about the user's brand, achievements, and content pillars. Use it to enrich recommendations, but Step 2 answers take priority.

### Hook Pattern Analysis

**10+ posts with engagement data:**

Extract hook patterns before writing:
1. Find the top 2-3 performing posts by impressions or comments
2. Identify common patterns — specific number, before/after contrast, counterintuitive statement, personal confession
3. Apply that pattern to the new hook. Do not deviate from proven patterns.

**0-5 posts:**

Not enough signal to analyze patterns. Generate **2 hook variants** in different styles (e.g. one number-led, one story-led) and frame it as an experiment:

> "Since you're still building data on what works for your audience, here are two different hook styles. Try one now, save the other for next time — and see which gets more traction."

## Step 4: Sharpen the Topic

Before writing, evaluate the idea for focus and hook potential. Make **one proactive suggestion** if there is a clear improvement — then wait for the user's reaction.

**Three moves, pick the right one:**

**1. Find the concrete anchor**
Is there a specific number, fact, or moment? If yes, anchor the hook there. If no, ask: "What's the most specific thing you remember about this? A time, a number, a moment that surprised you?"

**2. Narrow if too broad**
Signs: covers multiple tools/topics, no clear "before vs after", reads like a category overview.
Suggest: "This idea covers a lot. What's the ONE thing that surprised you most? Let's build around that."

**3. Expand by combining (dialectical move)**
Sometimes the idea is good but would be stronger combined with a complementary angle. Look for: an unexpected contrast, a broader pattern the specific story illustrates, a tension between two things.
Suggest only if the combination is genuinely stronger, not just bigger. The user decides.

**Do NOT start writing until there is a concrete anchor for the hook.**

## Step 5: Adapt to Profile Level

**Beginner (under 500 connections, low impressions):**
- 100-150 words, simple structure, one clear point
- No fancy formatting tricks, build credibility first

**Intermediate (500-1500 connections, or 500-1500 impressions/post):**
- 150-220 words, lists and structure allowed
- Bolder claims acceptable (if backed by experience)
- Start experimenting with hooks

**Advanced (1500+ connections, or 1500+ impressions/post):**
- 200-280 words, complex structures allowed
- Audience trusts the takes, can be more contrarian

### Reach Archetypes

When reach is the priority, help the user choose one of these two "engines":

1.  **The Vulnerability Engine (Social Velocity)**
    - **Draft signal:** Personal failure, mistakes, "I was wrong", real stats of personal struggle.
    - **Algorithmic trigger:** High "Reaction" count and early "Emotional Comments".
    - **Best for:** Fast reach boost, building trust, and "viral" spikes.
    - **Success metrics:** High impressions/hour even without attachments.

2.  **The Utility Engine (Dwell Time)**
    - **Draft signal:** How-to, "I built X", "How I automate Y", listicles.
    - **Algorithmic trigger:** High "Dwell Time" (PDF/Carousel) and "Saves".
    - **Best for:** Long-tail reach, professional positioning, and high "Save" counts.
    - **Success metrics:** High total impressions over 3-7 days.

## Step 6: Structure the Post

Every post needs three parts:

### Hook (First 2-3 lines)

This is the only part visible in the feed before "...more". The reader decides in 1-2 seconds: expand or scroll.

What makes someone stop:
- A specific number in the first line (proven: every top post starts with a number)
- A specific detail from experience
- A question that resonates
- A statement that challenges assumptions

NOT generic openers like "I've been thinking about...", "Here's what I learned...", "Let me share..."

### Body

The actual insight, story, or information. Structured for easy scanning (short paragraphs, lists if needed). Length depends on profile level.

**Links:** Never put URLs in the post body — LinkedIn deprioritizes posts with outbound links. Always suggest moving links to the first comment.

### Conclusion (1-2 lines)

**Intermediate and Advanced:** Always end with a question or call to comment. Comments are the #1 driver of algorithmic reach on LinkedIn — 40+ comments can mean 5-10x impressions.

Good endings:
- A specific question about the reader's experience
- A mild provocation that invites disagreement
- An open comparison

Bad endings:
- Generic "What do you think?" — too vague
- Just a takeaway with no question
- Multiple questions — dilutes focus

**Beginner:** A simple takeaway is fine — focus on clarity, not engagement hacking.

One question or CTA, not multiple.

## Step 7: AI Slop Check

Read `references/voice-guidelines.md` and apply all checks: language patterns, formatting red flags, voice check, toxic tone rules. Remove anything that fails.

## Step 8: Generate Output

Output format:

```
## Your Post

[The actual post text, ready to copy-paste]

---

## Why this hook

[1-2 sentences: what signal it sends, why it earns the "...more" click]

## Alternative hook (if there's a clearly different angle)

[First 2-3 lines only. Skip if the chosen hook is clearly the best fit.]

## First comment (if relevant)

[Links, Telegram channel, additional context — only if the user has one.
Never in the post body.]

## Quick stats

**Profile level:** [Beginner/Intermediate/Advanced]
**Length:** [word count]
**Tone:** [casual / technical / mixed]
```

## Step 9: Expert Review

**Intermediate and Advanced profiles:** Run automatically.
**Beginner profiles:** Offer it: "Want me to run this through an external reviewer for a second opinion?"

Review criteria to send to the external model:
1. **Hook strength** — would you click "...more"? Why or why not?
2. **AI slop check** — does anything feel machine-generated?
3. **CTA effectiveness** — does the ending make you want to comment?
4. **One specific suggestion** — what single change would make the biggest impact?

Present feedback to the user and offer to incorporate it.

## Step 10: Refine Mode

After generating the post (and optionally after expert review), enter an iterative refinement loop.

Ask: "What feels weak to you? Point at specific parts — hook, body, CTA, tone, anything — and I'll rework them."

**Rules:**
- Rework ONLY flagged parts — do not touch what works
- Show the updated post with changes highlighted
- Ask again: "Better? Or still something to fix?"
- Repeat until approval
- Never rewrite the entire post unless asked — surgical fixes only
- Preserve the user's voice and original ideas
- If user feedback conflicts with expert review, the user wins
- Track versions (v1 -> v2 -> v3)
- After 3+ rounds without landing, suggest: "Maybe the core idea needs a different angle? Let's try a fresh hook."

Exit refine mode when the user approves or moves on.

## Step 11: Reach Optimization

After the user approves the text (Step 10), perform a final "Reach Check" to maximize distribution:

### 1. Attachment Strategy: Screenshot vs Carousel

Before suggesting a carousel, check the user's top-performing posts (if `data/top-posts-analysis.md` exists, read it).

**Default recommendation: Single screenshot.**
- Top-performing posts consistently use a single informative screenshot (terminal, dashboard, analytics).
- A screenshot is lower friction to produce and doesn't risk the carousel dwell-time penalty on low-engagement posts.

**When to suggest a carousel (PDF Document):**
- The post is a **how-to with multiple steps** (install commands, before/after, tool comparison).
- The user explicitly wants maximum dwell time.
- The user already has carousel-ready content (slides, diagrams).

**If user chooses carousel, follow the Carousel Rules (Step 12).**

### 2. Niche Hashtags (Discovery)
Suggest 1-3 (max 3) niche hashtags. 
- **Rule:** Use them only for **Topic Categorization** (#engineeringmanagement, #obsstudio), not for "magic reach".
- **Why:** They help LinkedIn route the post to relevant interest groups but are secondary to engagement and dwell time.

### 3. CTA Opening Check
Analyze the closing question. If it's a binary "Yes/No" question (e.g., "Do you agree?"), suggest a more open-ended version that encourages longer comments.
- **Example:** Instead of "Do you use AI?" -> "What's the most surprising result an AI tool gave you this week?"

### Data Collection Tips

After delivering the post, suggest this only if the user seems engaged and has 3+ posts:

> To make future posts more tailored, share:
> 1. **Best posts** — paste 2-3 top performers with impression numbers
> 2. **Post Analytics Export** — LinkedIn -> Analytics -> Content -> Export
> 3. **Full LinkedIn Data Export** — LinkedIn -> Settings -> Data Privacy -> Get a copy of your data -> Select "Posts"

## Step 12: Carousel Rules

If the user wants a PDF carousel, follow these rules.

### Structure

1. **Slide 1 — Title.** One clear statement of what the reader will get. No generic taglines.
2. **Slide 2 — Why / Proof.** Personal result with a specific number. Answer: "why should I keep reading?"
3. **Slide 3 (optional) — Screenshot proof.** A real screenshot from Perplexity, ChatGPT, terminal, analytics — with key elements highlighted (red border). Visual proof > text claims.
4. **Middle slides — Content.** One idea per slide. Use markdown lists (`-`), not unicode bullets (`•`). Keep text scannable — a reader spends 3-5 seconds per slide.
5. **Second-to-last slide — Actionable step.** Install commands, links, or a concrete next action.
6. **Last slide — Contacts.** Always include LinkedIn profile + Telegram/other channels. Match the format from previous carousels (see `drafts/` for examples).

### Formatting for MarkText → PDF

- Use `<div style="page-break-after: always;"></div>` between slides (not `---`).
- Do NOT use `## Slide N:` labels — they render as visible headers in PDF.
- Use `##` for slide titles, `-` for lists, ` ``` ` for code blocks.
- Keep 6-8 slides total. More = lower completion rate.
- Test on mobile — LinkedIn carousels are mostly viewed on phones. If a screenshot has small text, crop to the key area.

### Content Rules

- **No AI slop.** Same rules as posts: no buzzwords, no "10 синих ссылок", no "game-changer".
- **Answer three questions:** WHY this tool/approach? WHAT does it do? HOW to set it up?
- **No redundancy with the post.** The post sells the problem and result. The carousel gives technical details and installation. They don't repeat each other.
- **Links go in the carousel, not the post.** Repository URLs, install commands — all in the carousel. Post stays clean for the algorithm.

### Expert Review for Carousels

When running expert review (Step 9), add this criterion:
- **"Why?" check** — Does the carousel answer why THIS specific tool/approach and not alternatives? "I tested it and it worked" is not enough. Include: how many alternatives exist, what makes these complementary, what gap they fill.

## Step 13: Learning the User's Style

The skill gets better when it knows what already works for the user. Don't hardcode file paths — ask.

### Gathering Post History

If the user has **3+ published posts**, ask them to share top-performing posts with stats. One message:

> "To write in your voice and hit your numbers, I need to see what already works. Can you share:
> 1. **2-3 top posts by impressions** — the text + impressions count
> 2. Or an **analytics export** from LinkedIn (Analytics → Content → Export)
>
> This helps me match your style, length, and hook patterns."

If the user shares data, analyze it for:
- **Hook patterns** — what opens the top posts? (numbers, stories, contrarian claims)
- **Optimal length** — average word count of top performers
- **Attachment type** — screenshots vs carousels vs text-only
- **CTA style** — what kind of endings drive comments
- **Topics** — what themes get the most reach

Save these patterns in the project for future sessions.

If the user has **0-2 posts** or doesn't want to share data, skip this step and focus on fundamentals: strong hook, clear body, actionable CTA.

### Posting Strategy (for users who ask)

**Frequency:**
- No more than 2 posts per week. The algorithm needs time to understand your core topic and build distribution. Posting daily dilutes signal.
- Space posts 3-4 days apart so they don't compete with each other.

**Topic focus:**
- Stick to maximum 2 related themes. LinkedIn's algorithm rewards topical consistency — it learns what your audience engages with and routes your posts to similar people.
- Writing about completely unrelated topics simultaneously confuses the algorithm and splits your audience.

**What gets reach:**
People engage with posts that are either:
1. **Useful** — solves a real problem, gives a tool, saves time
2. **Provocative** — invites disagreement, challenges assumptions, starts a discussion

Posts that are neither useful nor provocative get low reach regardless of length or formatting.

### CTA Calibration

Match the CTA to what the user is ready to deliver:
- If the user **won't create bonus materials** (PDFs, templates) in exchange for comments — don't suggest "drop a comment and I'll send you X". It creates a promise they won't keep.
- If the user **is active in comments** — suggest open-ended questions that spark discussion.
- If the user **is a beginner** — a simple takeaway is fine. No engagement hacking.

### Proven Patterns

These rules come from analyzing real post performance:

1. **Numbers in the first line — always.** Not "I spent time..." but "20k messages in 70 days", "$50/month", "9 interviews in 2 months".
2. **Optimal length: 150-200 words.** Going over 200 is fine for Advanced profiles but should be justified.
3. **Single screenshot > carousel** for pure reach. Carousels are better for dwell time but carry higher risk if engagement is low.
4. **Links in the first comment, never in the post body.** LinkedIn deprioritizes posts with outbound links.
5. **Personal data builds trust.** Real screenshots from dashboards, terminals, analytics — not stock images.
6. **Open-ended CTA, not binary.** "How many agents do you use?" > "Do you use AI agents?"
7. **Hashtags: max 3, topic-specific.** Use compound tags (#GEOSEO not #GEO). No generic tags (#technology, #innovation).
