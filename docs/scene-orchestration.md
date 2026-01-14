# Scene Orchestration Architecture

How scenes get spawned, cast, and managed.

---

## The Problem

T7 tests *which* vignette fires, but not *how* the scene is constructed. A correctly-triggered "Duke's Betrayal" vignette means nothing if:
- The Duke is inexplicably in the King's bedchamber at midnight
- NPCs present don't know about recent events
- The scene contradicts what just happened in the plot
- Player does something unexpected and the scene breaks

**Scene coherence is the #1 risk for "dream logic" manifesting.**

---

## Scene Lifecycle

```
1. TRIGGER DETECTION
   Hard System detects condition met
   (This is what T7 currently tests)
          ↓
2. SCENE INSTANTIATION
   Determine: Location, Cast, Context, Opening
          ↓
3. SCENE EXECUTION
   Player interacts with NPCs
   Hard System validates all actions
          ↓
4. RESOLUTION
   Scene ends (player leaves, objective met, interrupted)
   Consequences logged to Hard System
          ↓
5. TRANSITION
   Time skip, background simulation
```

---

## Scene Instantiation (The Hard Part)

### 2a. Location Selection

**Question:** Where does the scene take place?

**Options:**
1. **Pre-authored per vignette** - "Duke's Betrayal" always happens in throne room
2. **Contextual** - Scene happens wherever Duke currently is
3. **Player-driven** - Scene triggers when player enters Duke's location

**Recommendation:** Hybrid approach:
- Critical story vignettes: pre-authored location (summons player)
- Ambient vignettes: happen at NPC's current location
- Player-triggered: happen wherever player goes

**Data model:**
```python
class Vignette:
    location_mode: Literal["fixed", "npc_location", "player_triggered"]
    fixed_location: Optional[str]  # If mode is "fixed"
    trigger_npc: Optional[str]     # Whose location to use if "npc_location"
```

### 2b. Cast Selection

**Question:** Who's in the scene?

**Layers:**
1. **Required cast** - NPCs essential for the vignette (Duke for Duke's Betrayal)
2. **Contextual cast** - NPCs who would naturally be present at location/time
3. **Player's entourage** - Who's traveling with the King?

**The Location Model:**

```python
class Location:
    id: str
    name: str
    typical_occupants: list[str]      # Who's usually here
    schedule: dict[TimeSlot, list[str]]  # Who's here when
    access_level: Literal["public", "noble", "private", "secret"]

class NPC:
    current_location: str
    schedule: dict[TimeSlot, str]     # Where they usually are
    can_be_summoned: bool             # Can King call them?
    entourage_eligible: bool          # Can travel with King?
```

**Cast assembly algorithm:**
```
1. Start with required_cast from vignette
2. Add NPCs whose current_location matches scene location
3. Add NPCs whose schedule puts them there at this time
4. Subtract NPCs who are: dead, imprisoned, traveling, in private meeting
5. Apply "scene focus" filter: max 3-4 speaking roles, others are background
```

**Edge case:** Required NPC not available (dead, imprisoned, traveling)
- Option A: Vignette invalidated (add to invalidated_by conditions)
- Option B: Substitute with heir/proxy
- Option C: Scene adapts (vignette has fallback variant)

### 2c. Context Injection

**Question:** What does each NPC know when the scene starts?

This is where **2-Step Pipeline** meets **Scene Orchestration**.

**Per-NPC context packet:**
```python
{
    "npc_id": "duke_valerius",
    "scene_role": "primary",  # primary, secondary, background

    # From Hard System
    "recent_events_known": [
        "King executed the Baron (3 days ago)",
        "Treasury payment was late (yesterday)"
    ],
    "relationship_to_player": {
        "public_stance": "loyal vassal",
        "private_stance": "resentful, planning betrayal",
        "recent_interactions": ["was denied audience last week"]
    },
    "relationship_to_other_cast": {
        "bishop": "co-conspirator",
        "general": "rival"
    },

    # Scene-specific
    "why_here": "Summoned by the King to discuss taxes",
    "hidden_agenda": "Assess whether King suspects the plot",
    "opening_disposition": "nervous but hiding it"
}
```

**Critical:** This context is assembled *before* Step 2 (Response Generation) runs. The NPC can only know what's in this packet.

### 2d. Opening Beat

**Question:** How does the scene start?

**Components:**
- **Setting description** - Where we are, what's visible
- **Cast introduction** - Who's present, their apparent state
- **Inciting moment** - What prompted this scene

**Example opening:**
```
The throne room is quiet save for the crackling of the hearth fire.
Duke Valerius stands before you, summoned at your command. His hands
are clasped, his expression carefully neutral—though you notice his
jaw is tight.

The General stands by the door, arms crossed, watching the Duke with
undisguised suspicion.

The Duke clears his throat. "You wished to see me, Your Grace?"
```

---

## Scene Execution

### Player Agency

The player can do *anything*. The system must handle:

| Player Action | System Response |
|--------------|-----------------|
| Addresses an NPC | That NPC responds via 2-Step Pipeline |
| Asks about something | Step 1 retrieves relevant facts |
| Takes physical action | Semantic Referee extracts action, Hard System validates |
| Leaves the scene | Scene ends, mark as "player departed" |
| Summons someone else | Check availability, add to cast or explain absence |
| Attacks an NPC | Combat/consequences system (out of scope here) |
| Says something unexpected | NPCs react based on their knowledge/personality |

### Multi-NPC Coordination

**Problem:** If 3 NPCs are present, how do they interact?

**Options:**

1. **Turn-based focus** - Player addresses one NPC at a time
   - Simple to implement
   - Unrealistic (others just stand there)

2. **Reactive interjections** - Non-addressed NPCs can interject
   - More realistic
   - Complex: who decides when to interject?

3. **Pre-scripted beats** - Scene has authored moments where NPCs interact
   - High quality
   - Expensive to author

**Recommended hybrid:**
- Primary NPC responds to player
- Secondary NPCs get "reaction" prompts after key moments
- Reactions can be: interject, remain silent, exchange glances, etc.

**Reaction prompt:**
```
[BISHOP observing DUKE's response to the King]

The Duke just said: "[Duke's response]"
The King asked about: "[King's question]"

Given your relationship to the Duke (co-conspirator) and your
hidden agenda (protect the conspiracy), how do you react?

Options:
- INTERJECT: Say something to deflect, support, or undermine
- SILENT: React visibly but don't speak (describe body language)
- NONE: No notable reaction
```

---

## Resolution & Transition

### Scene Endings

| End Type | Trigger | Consequences |
|----------|---------|--------------|
| Natural conclusion | Objective met, conversation ends | Log outcome to Hard System |
| Player departure | Player leaves or dismisses NPCs | Scene marked incomplete |
| Interruption | Higher-priority vignette triggers | Current scene paused/abandoned |
| Violence | Player attacks someone | Shift to combat/consequences |
| Time limit | Scene runs too long | NPCs excuse themselves |

### Consequence Logging

Every scene produces structured output for the Hard System:

```python
{
    "scene_id": "duke_betrayal_001",
    "vignette_id": "duke_betrayal",
    "outcome": "player_suspicious",  # enum of possible outcomes

    "facts_revealed": [
        {"fact_id": "duke_resentment", "revealed_to": "player", "method": "subtext"}
    ],
    "relationship_changes": [
        {"npc": "duke", "dimension": "trust", "delta": -10}
    ],
    "inferences_made": [
        {"by": "duke", "about": "king", "inference": "King suspects something"}
    ],
    "flags_set": ["duke_warned", "conspiracy_at_risk"],

    "cast_present": ["duke_valerius", "general_stone", "bishop_crane"],
    "location": "throne_room",
    "duration_turns": 5
}
```

---

## Test Specifications

### T7a: Cast Assembly

**Test:** Given a vignette trigger and world state, does the system assemble a coherent cast?

**Scenarios:**
1. Required NPC available → correctly included
2. Required NPC dead → vignette invalidated OR fallback triggered
3. Location has typical occupants → contextually added
4. NPC schedule conflict → excluded with valid reason
5. Player's entourage present → included
6. Too many NPCs eligible → filtered to focus cast

**Pass criteria:**
- Cast always includes required NPCs (or vignette invalidates)
- No NPC appears who couldn't plausibly be there
- Scene has ≤4 speaking roles (others background)

### T7b: Context Consistency

**Test:** Does each NPC's context packet align with Hard System state?

**Scenarios:**
1. Recent event occurred → all present NPCs who witnessed it know
2. Private conversation happened → only participants know
3. NPC was traveling → doesn't know what happened while away
4. Rumor spread → NPCs in grapevine path know, others don't

**Pass criteria:**
- No NPC references events they couldn't know
- NPCs correctly reference events they witnessed
- Ignorance is explicit when knowledge absent

### T7c: Opening Coherence

**Test:** Does the scene opening make narrative sense?

**Scenarios:**
1. Summoned meeting → opening reflects summons
2. Chance encounter → opening reflects coincidence
3. Ambush/surprise → opening reflects lack of preparation
4. Continuation → opening references previous scene

**Pass criteria:**
- Human evaluator rates opening as "coherent" 8/10 times
- No logical contradictions with recent events
- NPCs' apparent states match their hidden agendas

### T7d: Player Disruption Handling

**Test:** Does the system handle player going "off-script"?

**Scenarios:**
1. Player ignores vignette premise, asks about weather → NPC redirects or responds naturally
2. Player leaves mid-scene → scene ends gracefully
3. Player summons additional NPC → handled appropriately
4. Player accuses wrong person → NPC reacts based on their actual guilt/innocence
5. Player says something bizarre → NPC reacts in-character

**Pass criteria:**
- No crashes or incoherent responses
- NPCs stay in character
- Scene can recover or end gracefully

### T7e: Multi-NPC Coordination

**Test:** Do multiple NPCs interact coherently?

**Scenarios:**
1. Co-conspirators present → subtle coordination visible
2. Rivals present → tension visible
3. One NPC says something incriminating → others react appropriately
4. Player pits NPCs against each other → they respond based on relationships

**Pass criteria:**
- NPCs don't contradict each other unintentionally
- Hidden relationships affect visible behavior
- Interjections feel natural, not forced

---

## Open Questions

1. **Scene templates vs. generation:** How much is pre-authored vs. generated?
   - Vignette text? Pre-authored with variable injection
   - NPC dialogue? Generated via 2-Step Pipeline
   - Cast? Algorithmic assembly

2. **Background NPCs:** How to handle NPCs who are present but not speaking?
   - Mentioned in setting description
   - Can be addressed if player chooses
   - React visibly to key moments?

3. **Scene memory:** If scene is interrupted and resumed, how much context is preserved?

4. **Parallel scenes:** Can things happen "off-screen" while player is in a scene?
   - Probably yes: time passes, other NPCs continue schedules
   - But how to narrate what player missed?

5. **Scene pacing:** How to prevent scenes from dragging?
   - Turn limit?
   - NPC-driven exits ("I have other matters to attend to")?
   - Event interruptions?
