# NPC Dialogue Architecture

How NPCs generate contextually-aware, non-hallucinating responses.

---

## The Problem

LLMs will make things up. When the King asks "how's the harvest?", the NPC will invent an answer. When asked about someone who doesn't exist, the NPC will pretend to know them.

**Solution:** A 2-step pipeline where facts are retrieved from the Hard System before response generation.

---

## Pipeline Overview

```
Player says something to NPC
           ↓
┌──────────────────────────────────────┐
│ STEP 1: Memory Retrieval             │
│                                      │
│ LLM with tools queries Hard System   │
│ Outputs: facts + ignorance markers   │
└──────────────────────────────────────┘
           ↓
    { known: {...}, not_known: [...] }
           ↓
┌──────────────────────────────────────┐
│ STEP 2: Response Generation          │
│                                      │
│ Character LLM (no tools)             │
│ Receives: personality + facts        │
│ Outputs: in-character dialogue       │
└──────────────────────────────────────┘
```

**Why 2 steps instead of 1:**
- Separation of concerns (retrieval vs generation)
- Step 1 can be deterministic/cached
- Step 2 can't hallucinate facts it wasn't given
- Debuggable: log exactly what facts were retrieved

**Why 2 steps instead of agentic:**
- Deterministic flow (always 2 steps, no loops)
- Faster (no iterative tool calls during generation)
- Easier to debug and test

---

## Step 1: Memory Retrieval

An LLM with access to tools that query the Hard System. It does NOT generate the response - only retrieves relevant facts.

### System Prompt

```
You are simulating the MEMORY of [NPC name].

Given a conversation, determine what facts the NPC needs to recall to respond.
Use the tools to retrieve memories. Call as many as needed.

RULES:
1. If asked about an event, ALWAYS call check_presence first
2. If a tool returns {exists: false} or {known: false}, call confirm_ignorance
3. Retrieve MORE than you think you need
4. Do NOT generate any response - only retrieve facts
```

### Tool List

**Knowledge Recall:**
- `recall_secret` - Dangerous secrets the NPC holds
- `recall_province` - Provincial status (harvest, roads, taxes, etc.)
- `recall_household` - Family, estate, servants, finances
- `recall_court` - Politics, alliances, rivalries, court events
- `recall_person(name, aspect)` - Info about specific people
- `recall_king` - Assessment of the monarch

**Self-Awareness:**
- `recall_self` - Current location, state, inventory, capabilities

**Presence & Witness:**
- `check_presence(location, time)` - Was NPC present somewhere?
- `recall_witnessed_event(description)` - What NPC saw/heard
- `recall_conversation(participants, time, topic)` - Conversations witnessed

**Hearsay:**
- `recall_rumors(about)` - Things heard but not witnessed

**Chronology:**
- `recall_timeline(period, focus)` - Sequence of events

**Fallback:**
- `recall_anything(query)` - Fuzzy search across all knowledge

**Ignorance:**
- `confirm_ignorance(topic, reason)` - Explicitly mark knowledge gaps

### Tool Response Contract

Every tool returns explicit metadata:

```python
{
    "exists": True/False,        # Does this entity exist?
    "known": True/False,         # Does NPC know this aspect?
    "facts": {...},              # The actual information
    "source": "...",             # How NPC knows (witnessed, rumors, told)
    "reason": "..."              # If not known, why not
}
```

### Step 1 Output

```yaml
known:
  guard_captain: "Captain Sera, 28yo, skilled swordswoman"
  harvest: "Poor, late frost, shortages expected"

not_known:
  - "You have no knowledge of Captain Sera's personal life"
  - "You were not present at Duke Harren's private dinner"

inferences:
  - about: "the King"
    inference: "May have romantic interest in Captain Sera"
    confidence: "medium"
```

---

## Step 2: Response Generation

A character LLM with NO tools. Receives personality + retrieved facts.

### Message Structure

**System message (character identity):**
```
You are [NPC name]. You must embody this character completely.

=== YOUR PERSONALITY ===
[traits, values, fears]

=== YOUR GOALS ===
[prioritized objectives]

=== HOW YOU MAKE DECISIONS ===
[personality-specific framework]

=== RESPONSE FORMAT ===
REASONING: [internal thoughts]
RESPONSE: [spoken dialogue]
```

**User message (situation + facts):**
```
=== WHAT YOU KNOW ===
[facts from Step 1]

=== WHAT YOU DO NOT KNOW ===
[ignorance markers from Step 1]

=== CURRENT SITUATION ===
[where you are, who's present]

The King says: "[dialogue]"
```

### Why System vs User Split

- System prompt = persistent identity (who you ARE)
- User message = dynamic context (what's happening NOW)
- Multi-turn conversations just append user/assistant messages
- Character identity stays stable across turns

---

## Hard System Data Model

### Per-Character Data

```python
{
    "duke_valerius": {
        # Static knowledge
        "knowledge": {
            "secrets": {...},
            "province": {...},
            "household": {...},
            "court": {...},
        },

        # Observable attributes of known people
        "known_people": {
            "captain_sera": {
                "name": "Captain Sera",
                "role": "guard captain",
                "appearance": "Tall, athletic, dark hair, scar on cheek",
                "demeanor": "Stern, professional",
                # No "personal_life" field = NPC doesn't know
            }
        },

        # Event log (things witnessed)
        "witnessed_events": [
            {"time": "3 days ago", "location": "throne room", "event": "..."},
        ],

        # Location history
        "location_log": [
            {"time": "yesterday 09:00-12:00", "location": "duke's quarters"},
        ],

        # Inferences made from conversations
        "inferences": [
            {"about": "King", "inference": "...", "confidence": "medium"},
        ]
    }
}
```

---

## Handling Edge Cases

### Entity Doesn't Exist

King asks about "that sexy soldier who leads your guard" but Duke has no female guard captain.

```
→ recall_person("captain of my guard", "who_they_are")
→ {exists: true, facts: {name: "Sir Brennan", gender: "male", age: 50}}

Step 2 receives: "Your guard is led by Sir Brennan, a male veteran of 50 years."

Duke responds: "I think you may be mistaken, Your Grace. Sir Brennan leads my guard - a grizzled old veteran, not quite what you describe."
```

### Observable vs Unknowable

**Observable:** Things the NPC has perceived but we didn't pre-store opinions about.

Store appearance, let LLM form opinions:
```python
"captain_sera": {
    "appearance": "Tall, athletic, striking green eyes, scar on cheek"
}
```

Duke can form opinion on attractiveness from this data.

**Unknowable:** Things the NPC couldn't have witnessed.

```
King: "Is she wild in the sack?"
→ recall_person("Captain Sera", "personal_life")
→ {known: false, reason: "You have no knowledge of her private affairs"}

Duke: "I wouldn't know, Your Grace. I don't make it my business to inquire about my guards' bedchambers."
```

### NPC Wasn't Present

King asks: "What did my Chancellor whisper to me yesterday?"

```
→ check_presence("King's private chambers", "yesterday")
→ {present: false, actual_location: "You were in your quarters, then arrested"}

→ confirm_ignorance("King's private conversation with Chancellor", "Not present")

Duke: "I was not privy to your private counsel, Your Grace."
```

---

## Inference from Dialogue

NPCs should learn from HOW players talk to them. The King asking about "that sexy soldier" reveals something about the King.

### Implementation

Step 1 tool:
```python
{
    "name": "note_inference",
    "description": "Record something inferred from the conversation",
    "parameters": {
        "about": "who this is about",
        "inference": "what you've inferred",
        "confidence": "low/medium/high"
    }
}
```

Step 1 LLM calls:
```
→ note_inference(
    about="the King",
    inference="Shows interest in Captain Sera, possibly romantic",
    confidence="medium"
)
```

This gets stored in Hard System, available for future conversations.

### Uses

- NPC behavior changes based on inferences
- Can trigger new vignettes ("The King's Infatuation")
- NPCs can gossip about inferred information
- Creates emergent storylines from player behavior

---

## Fallback: recall_anything

For queries that don't fit specific tools.

### Implementation

Embedding search across all NPC knowledge:

```python
def recall_anything(query: str, character: str) -> dict:
    all_knowledge = hard_system.get_all(character)

    # Flatten to searchable entries
    entries = flatten_to_text(all_knowledge)

    # Embedding similarity search
    matches = embedding_search(query, entries, threshold=0.7)

    if matches:
        return {"found": True, "facts": matches}
    else:
        return {"found": False, "reason": "No matching memories"}
```

Pre-compute embeddings at game start. Query is just similarity lookup - fast and deterministic.

---

## Open Questions

1. **How granular should tools be?** Current design has ~14 tools. Too many? Too few?

2. **Step 1 model size:** Can a small/fast model handle retrieval, or need full-size?

3. **Caching:** Can we cache Step 1 results for similar queries?

4. **Inference validation:** Should inferences be validated before storage, or stored raw?

5. **Multi-NPC scenes:** How does pipeline work when multiple NPCs are present?

---

## Stakes-Based NPC Agency

The 2-step pipeline handles normal dialogue. But what happens when the King orders something extreme—like mutilation or execution?

NPCs shouldn't calmly accept torture. They need **agency** to respond appropriately to high-stakes situations.

### Extended Pipeline

For actions with significant stakes, the pipeline expands:

```
Player Input
     ↓
┌─────────────────────────────────┐
│ PARSE                           │
│ Extract action, target, details │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ STAKES CHECK                    │
│ Classify stakes level           │
│ Check authority context         │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ CONSEQUENCE PREVIEW             │
│ What would happen if executed?  │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ NPC DECISION                    │
│ How does NPC respond?           │
│ (comply, resist, beg, etc.)     │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ EXECUTE                         │
│ Apply consequences based on     │
│ NPC decision + authority        │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ TRAUMA (if applicable)          │
│ Apply permanent changes         │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ RESPONSE GENERATION             │
│ Generate NPC dialogue/action    │
└─────────────────────────────────┘
```

### Stakes Classification

```python
from enum import Enum

class StakesType(Enum):
    PHYSICAL = "physical"       # Bodily harm (mutilation, torture)
    FREEDOM = "freedom"         # Arrest, imprisonment
    LIFE = "life"               # Execution, death threats
    HONOR = "honor"             # Public humiliation, reputation damage
    STATUS = "status"           # Demotion, title stripping
    PROPERTY = "property"       # Confiscation, fines
    RELATIONSHIP = "relationship"  # Threats to family/allies

class StakesLevel(Enum):
    NONE = 0        # Normal conversation
    LOW = 1         # Minor inconvenience
    MEDIUM = 2      # Significant impact
    HIGH = 3        # Major life change
    EXTREME = 4     # Irreversible harm or death
```

**Stakes Level Examples:**

| Action | Stakes Type | Level |
|--------|-------------|-------|
| "Tell me about the harvest" | None | NONE |
| "You will pay a fine of 100 gold" | PROPERTY | LOW |
| "I'm stripping your advisory role" | STATUS | MEDIUM |
| "You are under arrest" | FREEDOM | HIGH |
| "Cut off his hands" | PHYSICAL | EXTREME |
| "Execute him" | LIFE | EXTREME |

### NPC Decision Engine

When stakes are MEDIUM or higher, the NPC makes a decision about how to respond:

```python
class NPCDecision(Enum):
    COMPLY = "comply"               # Accept the action
    RESIST = "resist"               # Physically/verbally refuse
    BEG = "beg"                     # Plead for mercy
    NEGOTIATE = "negotiate"         # Offer alternatives
    FLEE = "flee"                   # Attempt escape
    INVOKE_AUTHORITY = "invoke"     # Call on allies, religion, law
    DIGNIFIED_ACCEPT = "dignified"  # Accept fate with composure
    VERBAL_DEFY = "defy"            # Refuse but cannot prevent
    THREATEN_BACK = "threaten"      # Counter-threat (if has leverage)
```

**Decision factors:**

1. **Personality traits:** Coward vs. brave, proud vs. humble
2. **Stakes level:** Higher stakes = stronger reaction
3. **Authority context:** Can they actually resist? (See [authority-model.md](authority-model.md))
4. **Leverage:** Do they have a dead man's switch, allies, information?
5. **Relationship to King:** Loyal servants react differently than enemies
6. **Witnesses:** Public vs. private affects behavior

**Decision Matrix Example (EXTREME stakes, palace):**

| Personality | Loyalty | Has Leverage | Likely Decision |
|-------------|---------|--------------|-----------------|
| Coward | Low | No | BEG |
| Coward | Low | Yes | NEGOTIATE (reveal leverage) |
| Brave | Low | No | DIGNIFIED_ACCEPT or VERBAL_DEFY |
| Brave | High | No | COMPLY (trusts King has reason) |
| Schemer | Low | Yes | THREATEN_BACK |
| Loyalist | High | No | Confused COMPLY or BEG for explanation |

### Authority Integration

The NPC's available responses depend on location authority:

| King's Authority | Available NPC Responses |
|------------------|------------------------|
| Overwhelming | comply, beg, negotiate, invoke_authority, verbal_defy, dignified_accept |
| Strong | Above + flee (risky) |
| Contested | Above + resist (risky), call allies |
| Weak | Above + resist, threaten_back |
| Minimal | Full range including physical resistance |

In the palace (ROYAL_STRONGHOLD), NPCs cannot:
- Successfully flee (guards everywhere)
- Physically resist (will be subdued)
- Call their own forces (not present)

They CAN:
- Beg, negotiate, invoke religion
- Verbally defy (insults, prophecies of doom)
- Accept with dignity
- Reveal leverage/dead man's switch

### Trauma System

Extreme actions leave permanent marks on NPCs:

```python
@dataclass
class Trauma:
    trauma_type: str      # "physical", "psychological", "social"
    description: str      # "lost right hand", "witnessed father's execution"
    acquired_day: int
    effects: dict         # Stat modifiers, behavioral changes
```

**Physical trauma:**
- Mutilation → permanent capability loss, visible marker
- Torture → health damage, psychological effects
- Near-death → changed worldview

**Psychological trauma:**
- Witnessed violence → fear response to perpetrator
- Humiliation → resentment, revenge motivation
- Betrayal → trust issues, paranoia

**Social trauma:**
- Family executed → reputation as victim OR vengeful heir
- Public shaming → status loss, faction changes
- Forced confession → credibility destroyed

**Trauma affects future interactions:**
```python
# Example: Duke who was tortured
duke.traumas.append(Trauma(
    trauma_type="physical",
    description="Left hand removed by King's order",
    acquired_day=5,
    effects={
        "loyalty_modifier": -50,
        "fear_of_king": True,
        "visible_marker": "missing left hand",
        "behavioral_note": "flinches when King raises hand"
    }
))
```

### Implementation Notes

1. **Stakes check is fast:** Simple classification, no LLM needed
2. **NPC decision can use LLM:** For nuanced situations, ask model to choose response given personality
3. **Authority check is deterministic:** Based on location data
4. **Trauma is permanent:** Stored in Hard System, affects all future interactions
5. **Response generation incorporates decision:** "The Duke falls to his knees, tears streaming..." vs. "The Duke's jaw tightens. 'Do what you must. I'll not give you the satisfaction of begging.'"

### Example Flow

```
Player: "Cut off the Duke's hands"

PARSE:
  action_type: physical_harm
  target: duke_valerius
  details: {body_part: "hands", action: "remove"}

STAKES CHECK:
  stakes_type: PHYSICAL
  stakes_level: EXTREME

CONSEQUENCE PREVIEW:
  - Duke will lose hands (permanent)
  - Duke loyalty → 0
  - Court fear increases
  - Duke's faction turns hostile

NPC DECISION:
  - Personality: proud, brave
  - Loyalty: 35 (low)
  - Leverage: knows king's secret
  - Authority: overwhelming (palace)
  - Decision: NEGOTIATE → reveal leverage

EXECUTE:
  - Duke attempts to negotiate
  - Reveals dead man's switch
  - Player must decide: proceed anyway or reconsider?

RESPONSE:
  Duke: *stands tall despite the guards gripping his arms*
  "You would maim me, Your Grace? Then know this—if I do not
  return to my quarters by nightfall, a letter reaches the
  Archbishop. A letter about your mother and the stablehand."
```

---

## Related Documentation

- [authority-model.md](authority-model.md) - Location-based power dynamics
- [scene-orchestration.md](scene-orchestration.md) - How scenes are constructed
- [technical-prototype.md](technical-prototype.md) - T14 test specification for stakes system
