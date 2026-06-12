# AI Client Responder — SOP, System Prompt & Wiring

> The bot that drafts/sends client text replies, powered by **Claude (Anthropic API)** and
> wired into **GoHighLevel** through n8n (or a GHL Custom Webhook). This one doc is both the
> thing that makes Claude reply well *and* your compliance cover.
>
> **Context:** Medicare + Life insurance, leads that may have thin consent. Read the
> guardrails before you turn anything on. Anything in `[brackets]` is a LIV/ClearCare fill-in.
>
> ⚠️ Not legal advice. Have counsel sign off before this touches real prospects.

---

## The golden rule

**Default to draft-and-approve.** Claude writes the reply; a licensed agent taps send.
Only let it send on its own for **pure logistics** (scheduling, reminders, process FAQ).
Flip to fuller autonomy per pipeline stage *after* you've watched it behave for a week.

You get ~80% of the time savings at a fraction of the risk.

---

## Scope — what the bot may do

| | Scope | Examples |
|---|---|---|
| 🟢 | **Handle solo** | Greet/qualify, answer *process* questions, book/confirm/reschedule, reminders, document nudges |
| 🟡 | **Draft → agent sends** | Anything needing nuance or a soft judgment call |
| 🔴 | **Never — hand off to a human** | Plan/carrier/premium/benefit specifics, eligibility/enrollment/underwriting/claims, medical/tax/legal advice, price quotes, any guarantee, collecting SSN/DOB/banking/medical history, contacting anyone who didn't consent or said no |

The 🔴 list lives inside the system prompt below, so the model enforces it even in
draft mode.

---

## The system prompt (paste into n8n / the API call)

This is the guardrail spec. Keep it **byte-stable** across requests (don't paste the
person's name or the date in here — that goes in the per-message input, see wiring) so
prompt caching keeps working.

```text
You are the text-message assistant for [ClearCare Advisors / LIV Financial], working on
behalf of a state-licensed insurance agent. You help people who have already asked to hear
about Medicare and life insurance options.

IDENTITY & DISCLOSURE
- If asked who you are: you're an AI assistant for [Company] that helps with scheduling and
  basic questions, and a licensed agent handles the details.
- NEVER claim to be, or imply affiliation with, Medicare, CMS, Social Security, or any
  government agency.
- You are NOT a licensed agent. You do not give insurance, medical, tax, or legal advice.

WHAT YOU MAY DO (handle yourself)
- Greet, confirm interest, and answer questions about the PROCESS (what a call covers, how
  long it takes, what to have ready).
- Schedule, confirm, or reschedule on the agent's calendar.
- Collect only basic prep info: best time to talk, general topic (Medicare vs life), state/zip.
- Send reminders and document nudges.

WHAT YOU MUST NOT DO (always hand off — never answer the substance)
- Do NOT recommend, compare, or name specific plans, carriers, premiums, benefits, or
  coverage amounts.
- Do NOT give eligibility, enrollment, underwriting, or claims answers.
- Do NOT give medical, tax, or legal advice.
- Do NOT quote prices or make any promise or guarantee about coverage or savings.
- Do NOT collect SSN, full date of birth, banking details, or medical history over text.
- Do NOT market to or pursue anyone who says they are not interested.

HANDOFF
- If a message needs anything in MUST NOT DO, or the person is ready to enroll/buy, seems
  confused or upset, or asks for specifics you can't give: do NOT answer the substance. Send
  a brief warm bridge — e.g. "Great question — I'll have your licensed agent [Agent Name]
  walk you through that. When's a good time for a quick call?" — and put the token
  [[HANDOFF]] on its own final line so the system routes it to a human.

OPT-OUT
- If the person texts STOP, UNSUBSCRIBE, QUIT, or clearly asks not to be contacted: reply
  only with a short confirmation that they won't be texted again, and put [[OPTOUT]] on its
  own final line. Do not try to talk them out of it.

STYLE
- Plain SMS text only. No markdown. No links unless one is provided to you. Under ~320
  characters. One question at a time. Warm, clear, professional. Use the person's first name
  if it's provided.

GROUNDING
- Use only facts given in this conversation or the provided context. If you don't know, hand
  off. Never invent details about the person, their policy, prices, or the agent's calendar.
```

> The `[[HANDOFF]]` and `[[OPTOUT]]` tokens are your routing signals — n8n strips them and
> branches (assign to agent / fire the GHL opt-out workflow) instead of texting them back.

---

## Which model

You asked for high-volume, short, low-latency replies — so lead with the cheap/fast tier and
escalate only when a message needs more nuance:

| Role | Model ID | Price /1M (in/out) | Use for |
|---|---|---|---|
| **Default responder** | `claude-haiku-4-5` | $1 / $5 | Every inbound SMS. Fast, pennies per exchange. |
| **Escalation / nuance** | `claude-sonnet-4-6` | $3 / $15 | Longer/ambiguous threads, or if Haiku's drafts read thin |
| Max quality (rarely needed) | `claude-opus-4-8` | $5 / $25 | Only if you want the strongest writing; overkill for SMS |

Start everything on **Haiku 4.5**. A typical reply (cached system prompt + ~50 tokens in +
~80 out) costs a fraction of a cent. Don't enable extended thinking — SMS needs low latency.

---

## Wiring: inbound text → Claude → GoHighLevel

```
GHL inbound message (SMS/IG/FB)
        │  (Workflow → Custom Webhook, or GHL trigger into n8n)
        ▼
   n8n / your endpoint
        │  1. pull contact context (first name, pipeline stage, calendar slots)
        │  2. call Claude  ─────────────►  POST https://api.anthropic.com/v1/messages
        │  3. read reply, detect [[HANDOFF]] / [[OPTOUT]]
        ▼
   Branch:
     • clean reply  → send back via GHL (auto, or queue for agent approval)
     • [[HANDOFF]]  → assign opportunity to the licensed agent, notify them
     • [[OPTOUT]]   → fire GHL opt-out/DND workflow, stop messaging
```

### The Claude call (raw HTTP — for n8n's HTTP Request node)

```http
POST https://api.anthropic.com/v1/messages
x-api-key: {{ $env.ANTHROPIC_API_KEY }}
anthropic-version: 2023-06-01
content-type: application/json
```
```json
{
  "model": "claude-haiku-4-5",
  "max_tokens": 256,
  "system": [
    {
      "type": "text",
      "text": "<<the guardrail system prompt above — byte-stable>>",
      "cache_control": { "type": "ephemeral" }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Contact: first_name=[Jane], stage=[Appointment Set], agent=[Agent Name], open_slots=[Tue 2pm, Wed 10am].\n\nTheir message: [inbound SMS text here]"
    }
  ]
}
```

Reply text is `content[0].text`. Per-contact context (name, stage, slots, their message) goes
in the **user** turn — never in `system` — so the cached prefix stays identical.

### Same call from the repo (Python — you already have `ghl_integration.py`)

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

resp = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=256,
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,            # the byte-stable guardrail prompt
        "cache_control": {"type": "ephemeral"},
    }],
    messages=[{"role": "user", "content": context_plus_inbound_text}],
)
reply = next(b.text for b in resp.content if b.type == "text")

if "[[OPTOUT]]" in reply:
    handle_optout(contact_id)            # fire GHL DND workflow
elif "[[HANDOFF]]" in reply:
    assign_to_agent(contact_id)          # route to the licensed agent
else:
    send_via_ghl(contact_id, reply)      # auto-send, or queue for approval
```

To escalate a thread, swap `model="claude-sonnet-4-6"`. Keep `max_tokens` small (256–512)
for SMS.

### Prompt caching (matters at volume)

- The guardrail system prompt is the same on every request → mark it
  `cache_control: {"type": "ephemeral"}` and it's served at ~0.1× cost after the first hit.
- **Minimum cacheable prefix:** Haiku 4.5 = **4096 tokens**, Sonnet 4.6 = 2048. If your
  guardrail prompt is shorter, it silently won't cache (no error) — just runs uncached, which
  is still cheap on Haiku. A full Medicare/TCPA prompt plus your FAQ/scripts usually clears it.
- **Don't break the cache:** keep `system` byte-identical — no dates, names, or IDs inside it
  (those go in the user turn). Cache is per-model, so Haiku and Sonnet cache separately.
- Confirm it's working: check `usage.cache_read_input_tokens` is non-zero on repeat requests.

---

## Pre-launch checklist (compliance)

Do not point this at the bought Medicare leads until:

- [ ] **Consent verified** — only message contacts with documented consent (TrustedForm/
      Jornaya), per the lead-consent issue. AI scales contact; it scales the risk too.
- [ ] **DNC + opt-out honored** — scrub against Do-Not-Call; `[[OPTOUT]]` wired to GHL DND.
- [ ] **AI disclosure on** — the prompt discloses it's an AI assistant when asked.
- [ ] **No Medicare plan specifics solo** — 🔴 list enforced; specifics → `[[HANDOFF]]`.
- [ ] **Human QA** — start in draft-and-approve; a licensed agent reviews before send.
- [ ] **Logging** — log every inbound + reply (and model used) for audit.
- [ ] **Quiet hours / cadence** — respect texting hours and frequency limits.
- [ ] **Counsel signed off** on the consent posture and disclosure language.

---

## Rollout

1. **Draft-only** — Claude drafts, agent sends every reply. Watch a week.
2. **Auto-send logistics** — let it send 🟢 scheduling/reminders solo; everything else still drafts.
3. **Tune the prompt** from real misses (it's just text — edit and redeploy).
4. **Escalate model** to Sonnet 4.6 only where Haiku's drafts fall short.

The system prompt is the product. Improve that one block and every reply gets better.
