# 09 · Devpost drafts

Drafts for the Devpost form. Checklist: [08-submission-checklist.md](08-submission-checklist.md).

## Basics

- **Name:** Kin
- **Tagline:** A private family care coordinator in Telegram: it remembers every document, reminds the right person, and tells no one who shouldn't know.
- **Track:** Personal AI. **Bonus:** Best Use of Tavily.
- **Built with:** NVIDIA Nemotron 3 Super, MiniCPM-V 4.5, Nebius Token Factory, Hermes Agent, Tavily, Telegram Bot API, Python, FastAPI, SQLite, Docker.

## Description

### Inspiration

When a parent comes home from hospital, the family's care runs on a group chat and a shoebox of paper. The daughter who handles it photographs the discharge letter, retypes the new medicine times for the helper, answers her brother's "what did the doctor change?" from memory, and decides, message by message, who should see the insurance letter. One in four adults is a caregiver; Singapore became super-aged this year. The hard part isn't storing documents; it's getting the right fact to the right person, and only to them.

### What it does

Kin lives in the family's Telegram group and in each member's DM.

- **Private intake.** The caregiver photographs a document in DM. Kin reads it, checks the draft against what it already knows (a medicine name that matches no record, a time that clashes with another letter) and asks one question at a time. Nothing is filed or scheduled until she confirms.
- **The schedule follows the documents.** Confirmed medicines become reminders on the helper's phone at the household's times. A replaced dose stops its old reminders; a course ends on its date; tomorrow's appointment is a reminder the evening before.
- **One update for everyone.** After she approves the exact text, the group gets a summary in English and Mandarin, holding only what every member may see.
- **Recall with sources.** "Kin, what did Dr Tan change at the last visit?" gets the answer with the doctor's own words quoted from the memo, and only from records that person may see.
- **Sharing on her terms.** A question about the insurance claim gets a neutral reply in the group. She gets a private request with buttons: share it, just this once, or not. The answer goes only to the asker, as the approved excerpt, never the original. `/who_saw` shows who was shown what.
- **A reusable skill.** "Every Monday at 8, remind Siti to refill the pill organiser and tell Mei Ling when it's done" runs from Kin's scheduler and survives restarts.
- **Public rules, no private data.** Questions about schemes such as the Home Caregiving Grant are looked up live on government sites through Tavily, with the link, without deciding eligibility and without sending a single family detail.

Kin organises; it never diagnoses, doses or triages.

### How we built it

Hermes Agent is the runtime and Telegram gateway; Nemotron 3 Super on Nebius Token Factory drives every conversation and writes the Mandarin posts; MiniCPM-V 4.5, also on Token Factory, reads the photos (Nemotron Nano Omni is dedicated-only). A small Hermes plugin passes the verified sender and chat to Kin's tools, routes photos, commands and button taps to Kin before any model runs, and sends every final reply past Kin's check. The kin service holds the records in SQLite and enforces a role × category policy with field projections before anything reaches the model, then again on the way out: a reply that contains something that chat may not see is withheld, and Kin itself attaches the approved excerpts and sources. Everything runs in one Docker Compose project with no published ports.

### Challenges we ran into

- Hermes gives MCP servers no caller identity, and Kin's every decision depends on who is asking, so we wrote a plugin that takes identity from the gateway session instead of tool arguments.
- On low-resolution photos of printed pages, the vision model read "Glibpizide" for "Glipizide". Kin now never trusts a medicine name that matches no record: it asks.
- Super translated medicine names (once into a different drug) and once claimed to have posted a message it had no way to post. Names are now masked during translation, and anything that has to be exact (requests for originals, old button taps) gets a fixed reply instead of a model's.
- One judge has to play both sides of a sharing request, so the demo lets one account hold every family seat, with messages labelled by recipient and a fresh conversation on every role switch.

### Accomplishments that we're proud of

- Validated live with two phones: a discharge summary photographed on paper became a confirmed schedule, the old reminders stopped, the helper's phone got the new ones, and they kept their place across a full restart.
- Boundaries in code, not prompts: retrieval, field projection, the reply check and the share flow are tested with forged identities, spoofed chats and a member asking for a mixed original.
- Running a family costs well under a dollar a month at list prices.

### What we learned

The model is best at the conversation and worst at being exact. Privacy, dosing times and claims about what was done belong in deterministic code around it; the model chooses tools and words.

### What's next

Visit debriefs from after-visit summaries, teach-by-chat skills, a weekly digest per role, and OpenShell isolation for the gateway.

## Testing instructions (private field)

- Bot: `@KinAgentBot`. Group: join with this invite link: `<invite link>`.
- Follow "Try it (judges)" in the README. One Telegram account plays the whole made-up family through `/demo`; nothing is real and no API key is needed.
- The video was recorded with two accounts; there the Admin is named Wenhao and Wei Jie fills the pill organiser. In the demo they are Mei Ling and Siti.
- Each tester starts with a fresh family. If someone else is mid-tour, Kin says so, and the demo frees up after 10 quiet minutes. `/demo reset` starts over; the demo also resets daily at 15:00 SGT (23:00 PST). Available until 16 Dec 2026, 04:00 SGT.

## Feedback

**Nebius Token Factory**
- Attempted: one OpenAI-compatible client for vision, answers and translation. Worked: 28 models listed; `response_format` JSON schema held for Super and Nano.
- Obstacle: Nemotron Nano Omni is dedicated-only, so there is no public NVIDIA model for photos or audio; we used MiniCPM-V 4.5 for photos and left audio out. Suggestion: a public, rate-limited Omni endpoint for hackathons. Impact: audio debriefs and an all-NVIDIA photo path were out of reach.
- Obstacle: MiniCPM-V and Super reason by default; with short `max_tokens` the visible output was truncated JSON. `chat_template_kwargs.enable_thinking: false` fixed it, but we found it by trial. Suggestion: document the thinking default and the switch on each model card.
- Observation: Nano took 17–21 s for a one-word classification on the public endpoint, slower than Super, so classification never became a live dependency.

**NVIDIA Nemotron 3 Super**
- Tool use was reliable once Kin's three tools were always in view; behind Hermes' tool search it skipped `kin_ask` and asked a clarifying question instead.
- In replies it sometimes printed citation markers such as `【{"id":"rec-…"}】`, translated drug names unless masked, and once claimed an action it had no tool for. Suggestion: a decoding or system-prompt option that suppresses citation markers in user-facing text.

**Hermes Agent v0.21.7**
- MCP tool calls carry no caller identity, so identity-bound tools need a plugin. Suggestion: pass the session's platform, user and chat to MCP servers, as plugins get them.
- `transform_llm_output` made a reply check possible; streaming and interim messages bypass it, so both must be off. Suggestion: document that, or apply the hook to interim text.
- The Telegram adapter registers about 60 Hermes commands even when a plugin answers every command; we set per-chat menus to hide them. Resetting a user's conversation from a plugin needs the session store's private API. Unauthorised DMs are dropped before `pre_gateway_dispatch`, so a plugin can't greet a newcomer without allowing all users.

**Tavily**
- `include_domains: ["gov.sg", …]` matched subdomains (ask.gov.sg, www.moh.gov.sg), exactly what a locale allow-list needs. An older MOH press release with superseded grant criteria ranked next to the current AIC page. Suggestion: return a published date with each result, or allow a recency filter with `include_domains`, so assistants can prefer current rules.
