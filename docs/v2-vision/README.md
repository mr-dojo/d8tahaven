# V2+ Vision Documents

**Purpose**: This directory contains design documents for **future features** not included in V1.

**Status**: Reference only - do not implement until V1 ships and proves value.

---

## What's In This Directory

Comprehensive specifications for features we're **deferring to V2+**:

- **browser-plugin-full.md** - Complete command palette + ghost button UX (1,381 lines)
- **enrichment-pipeline.md** - Stage 2 LLM tasks (classification, keywords, themes)
- **intelligence-layer.md** - Stage 5 synthesis and insights
- **full-schema.md** - All 9 tables (keywords, themes, relationships, etc.)

---

## Why These Are Deferred

**V1 Principle**: Ship working capture + retrieval first, prove value, then add intelligence.

These features are **well-designed but not essential** for proving the core hypothesis:
> "Personal AI memory improves LLM conversations"

**V1 tests this with**: Simple capture → Storage → Semantic retrieval

**V2+ adds**: Advanced UX, automatic enrichment, relationship detection, weekly synthesis

---

## When to Reference These Docs

**Read these when**:
- V1 is shipped and working
- You're using it daily and hit limitations
- You know what features matter most
- You're ready to add complexity

**Don't read these when**:
- You're implementing V1
- You're tempted to add "just one more feature"
- You're procrastinating on building V1
- You haven't proven V1 works yet

---

## V1 vs V2 Scope

### ✅ V1 (Shipping Now)

**Capture**:
- POST /v1/capture (text)
- POST /v1/capture/file (PDF/DOCX/TXT)

**Storage**:
- content_items table
- embeddings table (OpenAI)

**Retrieval**:
- POST /v1/retrieve/semantic (vector search)
- GET /v1/retrieve/recent (chronological)

**Browser Extension**:
- Simple popup with textarea
- Save button
- Search + copy to clipboard

**Architecture**:
- Synchronous capture (2-3 sec response)
- No Celery queue yet
- PostgreSQL + pgvector

### 🔮 V2+ (Future)

**Capture**:
- Command palette (⌘⇧Space)
- Ghost button (clipboard capture)
- Double-tap shortcuts
- Status tracking endpoint

**Enrichment** (Stage 2):
- Async Celery task queue
- LLM classification
- Keyword extraction
- Theme detection
- Relationship mapping
- Automatic summarization

**Storage** (Enhanced):
- keywords + keyword_occurrences tables
- themes + theme_memberships tables
- relationships table
- synthetic_content table
- capture_status tracking

**Retrieval** (Enhanced):
- Context packaging (optimize for LLM)
- Hybrid search (semantic + keyword)
- Temporal search (date ranges)
- Theme-based retrieval

**Intelligence** (Stage 5):
- Weekly synthesis
- Theme trend analysis
- Gap detection
- Connection recommendations

**Browser Extension** (Enhanced):
- Inline context injection (no clipboard)
- Recent items preview
- Settings page
- Keyboard shortcuts
- Auto-capture suggestions

---

## The Temptation

When building V1, you will be tempted to add features from these docs:

- "The command palette would only take a few hours..."
- "I should add keyword extraction while I'm here..."
- "The theme detection is so elegant, let me just..."

**Resist.** These are **future-you problems**.

**Present-you problem**: Make capture + retrieval work.

---

## How to Use These Docs

### Pattern: "V1 Works, What's Next?"

1. Use V1 yourself for 2 weeks
2. Document frustrations and missing features
3. Come back to these docs
4. Pick ONE feature that solves your biggest pain
5. Implement it
6. Use for 2 more weeks
7. Repeat

### Anti-Pattern: "V1 Isn't Done, But V2 Features Look Cool"

1. Start building V1
2. Read these docs for "context"
3. Notice command palette is well-designed
4. Spend 3 days implementing it
5. V1 still doesn't work
6. Burn out
7. Abandon project

**Don't do this.**

---

## Success Criteria for Reading V2 Docs

You should ONLY read these docs if you can answer "YES" to all:

- [ ] V1 is fully implemented and working
- [ ] I've been using V1 myself for at least 1 week
- [ ] I've identified a specific limitation in V1 that blocks me
- [ ] I know which V2 feature would solve that limitation
- [ ] I'm committed to shipping V1 before adding V2 features

If you answered "NO" to any of these, **close this directory and go back to building V1**.

---

## File Inventory

| File | Lines | What It Specifies | When to Implement |
|------|-------|-------------------|-------------------|
| browser-plugin-full.md | 1,381 | Command palette + ghost button UX | After V1 proves valuable |
| enrichment-pipeline.md | TBD | LLM classification, keywords, themes | After you need smarter search |
| intelligence-layer.md | TBD | Weekly synthesis, insights | After you have months of data |
| full-schema.md | TBD | All 9 tables with relationships | As needed per feature |

---

## Remember

**Good products are built iteratively, not comprehensively.**

V1 doesn't need to be perfect. It needs to work.

V2 doesn't need to be planned. It needs to solve V1's real problems.

**Stay focused. Ship V1. Use it. Learn. Then come back here.**

---

_"Premature optimization is the root of all evil." - Donald Knuth_

_"Premature feature-itis is the root of all abandoned projects." - Every developer who over-planned_
