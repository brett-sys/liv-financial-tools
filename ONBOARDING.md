# New Recruit Onboarding — Video Series Script

> **Purpose:** Record each module once. Send new recruits one playlist link instead of
> re-explaining the same thing every day.
>
> **How to use this doc:** Each module below is a recording script — read the talking
> points on camera while you share your screen. The **"Show on screen"** list is your
> b-roll checklist; the **"Recruit is done when"** box is what they should be able to do
> before moving to the next video.
>
> Anything in `[brackets]` is a fill-in-the-blank for LIV specifics (your numbers, your
> vendors, your comp) — replace it before recording.

**CRM:** Go High Level (Elite 360) &nbsp;•&nbsp; **Tools:** PDF Generator, Underwriting, Agent Toolkit (Quoter / Scoreboard / Call Logger / Referrals), Lead Manager, Password Vault

---

## Before you record (one-time setup)

- [ ] Make a private YouTube/Loom playlist called **"LIV — Start Here"**
- [ ] Record modules in order A → I
- [ ] Pin the playlist link in your recruiting chat / send it on day one
- [ ] Re-record a single module any time a tool or process changes (don't redo the whole series)

> **Keep this separate from `SETUP_GUIDE.md`.** That guide is the *developer* setup for the
> Python tools (Cursor, Python, WeasyPrint). Most recruits are agents, not developers — only
> send them the dev guide if they'll be running the desktop tools themselves.

---

## Module A — Account Setup & Access

**Goal:** Recruit can log into everything and is reachable through the CRM.

**Show on screen:**
- Go High Level login → **Settings**
- Calendar / availability (set their working hours)
- My Profile (name, photo, signature)
- **Wallet & Billing** — explain what they get charged for: `[phone/SMS usage, email, lead costs]`
- Phone number provisioning + a test text
- Email connection (so Conversations sends from their address)
- Password Vault for carrier-portal logins

**Talking points:**
- "This is your home base — if it's not in the CRM, it didn't happen."
- "Your calendar here is what clients book into. Set real hours so you don't get 7am calls."
- "The wallet is prepaid — `[explain how it gets funded and roughly what a text/call costs]`."

> **Recruit is done when:** they can log in, send themselves a test text from Conversations,
> and their calendar shows correct availability.

---

## Module B — CRM Tour ("What's What")

**Goal:** Recruit can navigate GHL without you driving.

**Show on screen:**
- Dashboard overview
- **Contacts** + Smart Lists
- **Conversations** (text, email, and calls in one inbox)
- **Calendar** (appointments view)
- **Opportunities / Pipeline** — the board where every deal lives

**Talking points:**
- "Five things you'll touch daily: Contacts, Conversations, Calendar, Opportunities, Dashboard."
- "Opportunities is the scoreboard for your deals — every client sits in exactly one stage."
- Save the deep dive on stages for Module D — here just point at the board.

> **Recruit is done when:** they can find a contact, open its conversation, and locate the
> pipeline board.

---

## Module C — Leads: Where They Come From & How to Work Them

**Goal:** Recruit can get a lead in front of them and make first contact fast.

**Show on screen:**
- Where leads originate: `[LeadConduit / landing page / referrals / purchased vendors]`
- **Lead Manager** tool — claiming / importing leads to an agent (`python -m lead_manager`, port 5070)
- The dialer + logging a call (Agent Toolkit Call Logger, `python agent_toolkit/app.py`, port 5055)

**Talking points:**
- "Speed is everything. Our rule: first dial within `[X minutes]` of a lead coming in."
- "Every attempt gets logged — no exceptions. That's how we know what's working."
- "A lead you don't log is a lead the team can't help you close."

> **Recruit is done when:** they've claimed a test lead, dialed it, and logged the outcome.

---

## Module D — The Sales Process (Client Pipeline)

**Goal:** Recruit can walk a client from "new lead" to "issued policy" and knows what each
stage means.

**Show on screen:**
- The Opportunities board, stage by stage
- Move one test client through each stage live

**Talking points — narrate each stage and what moves a client forward:**
1. **New Lead** → fresh, not yet attempted
2. **Attempted** → dialed, no contact yet (keep following the cadence)
3. **Contacted** → live conversation happened
4. **Appointment Set** → booked on the calendar
5. **Presented / Quoted** → you showed an illustration or quote
6. **Application Submitted** → e-app sent to the carrier
7. **Issued / Active** → policy approved and in force
8. **Referral Requested** → you asked for referrals

> See **`CLIENT_PIPELINE.md`** for the one-page cheat sheet + the exact stage names to paste
> into GHL.

> **Recruit is done when:** they can explain, in their own words, what action moves a client
> from each stage to the next.

---

## Module E — Quoting & Illustrations

**Goal:** Recruit can pick the right carrier and put a professional illustration in the
client's hands.

**Show on screen:**
- **Underwriting tool** (`python underwriting/underwriting_tool.py`) — enter health factors,
  read the carrier + rating-class results
- **Quoter** (Agent Toolkit)
- **PDF Generator** (`python -m pdf_generator`) — build an IUL illustration / quote comparison
- Sending it: the PDF auto-uploads to the client's GHL contact and can trigger a workflow

**Talking points:**
- "Underwrite first, quote second. The tool tells you who'll actually approve this client."
- "When you generate the PDF, it lands on the contact in GHL automatically — no manual upload."

> **Recruit is done when:** they've run a mock client through underwriting and generated one
> illustration PDF.

---

## Module F — Closing & Submitting Business

**Goal:** Recruit can take a yes and turn it into a submitted application.

**Show on screen:**
- The e-app / carrier portal `[which carriers you start new agents on]`
- Generating the **"Policy Submitted"** confirmation PDF
- The GHL workflow that fires after submission

**Talking points:**
- "The sale isn't done at 'yes' — it's done when the app is submitted and confirmed."
- "Move the opportunity to **Application Submitted** the moment you hit send."

> **Recruit is done when:** they can describe the submit flow end-to-end for `[your primary carrier]`.

---

## Module G — After the Sale

**Goal:** Recruit protects the policy and turns one client into more.

**Show on screen:**
- Policy delivery
- **Referral Tracker** (Agent Toolkit / PDF Generator) — logging and following up referrals
- Follow-up cadence for persistency `[your retention touchpoints]`

**Talking points:**
- "Best time to ask for a referral is right after they feel taken care of."
- "Persistency is your paycheck's best friend — a policy that stays on the books pays you twice."

> **Recruit is done when:** they've logged a referral in the tracker.

---

## Module H — Getting Paid

**Goal:** Recruit understands how and when money shows up.

**Show on screen:**
- `[Carrier commission portal / statements]`
- The wallet / ledger

**Talking points:**
- "Here's how comp works: `[advance vs. as-earned, your comp level, charge-backs]`."
- "This is why we submit clean apps — `[chargeback explanation]`."

> **Recruit is done when:** they can read a commission statement and explain advance vs. as-earned.

---

## Module I — Daily Routine & Scoreboard

**Goal:** Recruit knows exactly what a productive day looks like and how it's measured.

**Show on screen:**
- The **Scoreboard** (Agent Toolkit) — activity + outcomes
- The weekly export / accountability rhythm

**Talking points — your Daily Method of Operation (DMO):**
- `[X]` dials &nbsp;•&nbsp; `[X]` talk-time minutes &nbsp;•&nbsp; `[X]` appointments set &nbsp;•&nbsp; `[X]` apps written
- "We review the Scoreboard `[daily/weekly]`. Activity is the one thing you fully control."

> **Recruit is done when:** they know their daily numbers and where to see them on the Scoreboard.

---

## Optional Module J — Building Your Team

For recruits who'll recruit. Keep it short: "When you're ready to build, you send a new
person *this exact playlist*." That's the whole point — onboarding that duplicates itself.

---

*Record it once. Send the link. Get your day back.*
