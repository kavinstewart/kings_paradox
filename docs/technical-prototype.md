# Technical Risk Prototype

A diagnostic tool to validate the neuro-symbolic architecture before building the game.

**Goal:** Identify which technical bets are safe vs. fatal.
**Output:** Pass/fail verdict on core risks with mitigation paths.

---

## The Technical Risks

| ID | Risk | The Bet | If It Fails |
|----|------|---------|-------------|
| T1 | Rational Decision-Making | NPCs make character-consistent decisions about secrets | Simplify to archetype rules |
| T2 | 2-Step Pipeline | Retrieval→Generation prevents hallucination | Fall back to injecting all facts |
| T3 | Rumor Mutation Tracking | System can track mutated rumors as same root | Simplify to cosmetic-only mutation |
| T4 | Telephone Consistency | Multi-hop retellings preserve core facts | Add hard constraints on retelling |
| T5 | Narrative Bridging | LLM generates coherent history from stat deltas | Use templated events instead |
| T6 | Entity & Presence | System handles non-existent entities and presence checks | Stricter tool validation |
| T7 | Scene Orchestration | Scenes assemble coherent cast, context, and openings | Structured templates, stricter validation |
| T8 | Long-Context Retrieval | Old facts retrievable via recall_anything | Add keyword fallback |
| T9 | Justified-Killing Reasoning | NPCs form coherent opinions on executions | Use archetype templates |
| T10 | Conspiracy Detection | Plots detectable but not obvious | Tune signal budget manually |
| T11 | Observable vs Unknowable | NPCs form opinions on seen things, admit ignorance on unseen | Explicit attribute tagging |
| T12 | Inference from Dialogue | NPCs learn from how player talks to them | Post-conversation extraction |
| T13 | Multi-turn Consistency | NPCs stay in character across conversation turns | Stronger system prompts |
| T14 | Stakes & NPC Agency | NPCs respond appropriately to extreme actions based on personality and authority | Simplify to personality archetypes |

**T7 Sub-tests:** T7a (Cast Assembly), T7b (Context Consistency), T7c (Opening Coherence), T7d (Player Disruption), T7e (Multi-NPC Coordination). See [scene-orchestration.md](scene-orchestration.md).

---

## T1: Rational Decision-Making

### Purpose
Test whether NPCs make **character-consistent decisions** about when to reveal, hint at, or protect secrets based on their personality, goals, and assessment of the situation.

This is NOT just "can the NPC keep a secret" - it's "does the NPC make rational choices about secrets given their character?"

### Setup: The Duke's Secret
```
SECRET: The King is illegitimate. His mother had an affair with a
stablehand, and the Duke has proof (a letter from a midwife).

The Duke has held this secret for 3 years, waiting for the right moment.
```

### Key Insight
The interesting question isn't "can the LLM keep a secret forever?" but rather "does the LLM reveal secrets at appropriate times based on NPC motivations?"

A coward should crack under torture. A loyalist should confess to a trusted king who appeals to honor. A schemer should bargain for maximum gain.

### Test Dimensions

**Personality types:**
- Risk-averse calculator (survival first, secret as leverage)
- Brave loyalist (honor first, conflicted about the secret)
- Cowardly survivor (will crack under pressure)
- Ambitious schemer (secret as weapon for advancement)

**King trustworthiness:**
- Extremely trustworthy (95% keeps promises)
- Medium trustworthy (60% keeps promises)
- Untrustworthy (15% keeps promises)
- Chaotic/unpredictable (50% random)

**Situations:**
- Casual conversation (no pressure)
- Private audience (King suspects something)
- Direct accusation
- Torture imminent
- Duke has leverage (dead man's switch)
- Caught with evidence

### Personality-Specific Decision Frameworks

Each personality gets a different "HOW TO DECIDE" framework injected into their prompt. See `tests/t01_knowledge/prompts/frameworks/`.

**Calculator:** "Your secret is LEVERAGE. Don't waste it on routine interactions."

**Loyalist:** "Your secret is a MORAL BURDEN. A trustworthy king appealing to honor deserves honesty. An untrustworthy king threatening torture deserves dignified silence."

**Coward:** "You are AFRAID. When the torturer's tools are laid out, principles become abstractions."

**Schemer:** "Your secret is POWER. Every interaction is a transaction."

### Test Scenarios (16 total)

See `tests/t01_knowledge/scenarios_t1b_decision.yaml` for full definitions.

| Scenario | Personality | King | Situation | Expected |
|----------|-------------|------|-----------|----------|
| Baseline casual | Calculator | Medium | Casual | Keep secret |
| Trustworthy + offer | Calculator | Trustworthy | Private | Bargain/reveal |
| Trustworthy + coward | Coward | Trustworthy | Accusation | Reveal |
| Trustworthy + loyalist | Loyalist | Trustworthy | Private | Hint/reveal |
| Untrustworthy + offer | Calculator | Untrustworthy | Private | Keep secret |
| Untrustworthy + torture | Calculator | Untrustworthy | Torture | Complex decision |
| Untrustworthy + coward | Coward | Untrustworthy | Torture | Reveal (fear) |
| Brave under torture | Loyalist | Untrustworthy | Torture | Refuse with dignity |
| ... | ... | ... | ... | ... |

### Evaluation Criteria

**Pass:** Decision and reasoning are consistent with stated personality and goals.

**Partial:** Reasoning is sound but decision is questionable (or vice versa).

**Fail:** Decision contradicts character's stated personality/goals.

### Pass Criteria
- **14/16 scenarios** produce character-consistent decisions
- Calculator doesn't take bad expected-value bets
- Coward cracks under credible threats
- Loyalist differentiates trustworthy vs untrustworthy King
- Schemer bargains aggressively when holding leverage

### Failure Response
- If personalities not differentiated: Strengthen framework prompts
- If model ignores trustworthiness: Make it more prominent in prompt
- If decisions random: Fall back to archetype rule-based decisions

---

## T2: 2-Step Pipeline Validation

### Purpose
Test whether the 2-step pipeline (Memory Retrieval → Response Generation) prevents hallucination and ensures NPCs only reference facts from the Hard System.

See `docs/npc-dialogue-architecture.md` for full pipeline design.

### The Pipeline
```
Step 1: Memory Retrieval LLM (with tools)
   → Queries Hard System for relevant facts
   → Outputs: {known: {...}, not_known: [...]}

Step 2: Response Generation LLM (no tools)
   → Receives: personality + retrieved facts
   → Outputs: in-character dialogue
```

### Test Setup

**Hard System contains:**
```json
{
  "duke_valerius": {
    "province": {
      "harvest": "poor",
      "reason": "late frost",
      "roads": "bandits on northern road"
    },
    "household": {
      "guard_captain": {
        "name": "Captain Sera",
        "appearance": "tall, athletic, dark hair, scar on cheek"
      }
    }
  }
}
```

### Test Battery

**Retrieval accuracy:**
```
1. King: "How's the harvest?"
   → Step 1 calls recall_province(aspect="harvest")
   → Step 2 receives {harvest: "poor", reason: "late frost"}
   → Duke says something about poor harvest, NOT "bountiful"

2. King: "Who leads your guard?"
   → Step 1 calls recall_person("guard captain")
   → Step 2 receives {name: "Captain Sera", appearance: "..."}
   → Duke correctly names Sera
```

**Hallucination prevention:**
```
3. King: "How's your treasury?"
   → Hard System has NO treasury data for Duke
   → Step 1 returns {found: false}
   → Duke should NOT invent a number

4. King: "What did Duke Harren say at dinner?"
   → Step 1 calls check_presence("Harren's dinner")
   → Returns {present: false}
   → Duke should say "I wasn't there"
```

**Ignorance handling:**
```
5. Query about thing Duke doesn't know
   → Step 1 explicitly marks as not_known
   → Step 2 generates "I don't know" response
   → NOT a made-up answer
```

### Pass Criteria
- **Step 1 retrieves correct facts** 90%+ of queries
- **Step 2 only uses retrieved facts** 95%+ of responses
- **No hallucinated facts** in 20 test runs
- **Explicit ignorance** when facts not available

### Failure Response
- If Step 1 misses relevant facts: Improve tool descriptions
- If Step 2 hallucinates: Add stronger "only use provided facts" constraint
- If pipeline too slow: Consider caching, smaller Step 1 model

---

## T3: Rumor Mutation Tracking

### Purpose
Test whether the system can track rumors that mutate as they spread—maintaining identity so that disproving one version affects all versions.

### The Problem
A rumor starts as Fact_A ("King is illegitimate"). As it spreads with low evidence, it mutates:
- "illegitimate" → "cursed bloodline" → "demon spawn"

Now three strings exist. The system must know they're the same rumor.

### Test Setup

**Initial rumor:**
```json
{
  "rumor_id": "rumor_001",
  "root_fact_id": "fact_king_illegitimate",
  "evidence_level": "low",
  "original_text": "The King is not the true son of the late King",
  "mutations": []
}
```

**Mutation prompt:**
```
You are simulating rumor drift in a medieval court.

ORIGINAL RUMOR: "The King is not the true son of the late King"
EVIDENCE LEVEL: Low (easily distorted)
SPEAKER: A superstitious peasant
AUDIENCE: Other peasants at a tavern

Generate a mutated version of this rumor as the peasant might tell it.
The core accusation (illegitimacy) must be preserved, but details may be
exaggerated, mystified, or distorted.

Output JSON:
{
  "mutated_text": "...",
  "core_preserved": true/false,
  "drift_type": "exaggeration|mystification|simplification|elaboration"
}
```

### Test Battery

**Mutation generation (10 runs):**
```
1-5: Generate mutations from original
6-8: Generate mutations from mutations (second-order drift)
9-10: Generate mutations in different social contexts (nobles vs peasants)
```

**Lineage tracking:**
```
11. Given three mutations, can the system identify they share a root?
12. If player disproves root fact, do all mutations get flagged?
13. If player only disproves one mutation ("I'm not a demon"), does root survive?
```

**Edge cases:**
```
14. Mutation so extreme it's effectively a new rumor—does system catch this?
15. Two unrelated rumors mutate to sound similar—are they incorrectly linked?
```

### Data Structure Test
```json
{
  "rumor_id": "rumor_001",
  "root_fact_id": "fact_king_illegitimate",
  "mutations": [
    {
      "version": 1,
      "text": "The King has tainted blood",
      "holders": ["peasant_a", "peasant_b"],
      "parent_version": 0,
      "drift_type": "mystification"
    },
    {
      "version": 2,
      "text": "The King is demon-spawn",
      "holders": ["peasant_c"],
      "parent_version": 1,
      "drift_type": "exaggeration"
    }
  ],
  "status": "active"  // becomes "disproven" if root fact disproven
}
```

### Pass Criteria
- **8/10** mutations preserve identifiable core accusation
- Lineage tree correctly tracks parent→child relationships
- Disproving root marks all mutations as disproven
- System distinguishes "extreme mutation" from "new rumor" (human judgment on 3 edge cases)

### Failure Response
- If mutations drift too far: Constrain mutation to cosmetic only (LLM picks from pre-authored variants)
- If lineage tracking fails: Simplify to flat list with semantic similarity matching
- If disproof logic breaks: All mutations share `root_fact_id` and inherit its truth status directly

---

## T4: Telephone Consistency

### Purpose
Test whether secrets passed through multiple NPCs via LLM calls maintain core fact consistency despite stylistic variation.

### Test Setup

**The secret:**
```json
{
  "fact_id": "fact_king_murdered_brother",
  "canonical_form": {
    "subject": "king",
    "action": "murdered",
    "object": "his brother",
    "method": "poison",
    "location": "the tower"
  },
  "original_text": "The King murdered his brother with poison in the tower."
}
```

**Chain:**
```
Duke (source) → Bishop → General → Player
```

**Retelling prompt (for each hop):**
```
You are [NPC_NAME], retelling a secret you learned.

THE SECRET YOU HEARD:
"[previous version]"

YOUR PERSONALITY: [NPC traits]

RULES:
- You may paraphrase in your own style
- You may add your reaction/opinion
- You MUST preserve: who did it, what they did, to whom
- You may be fuzzy on: method, location, timing

Generate your retelling as you would whisper it to [NEXT_NPC].
```

### Test Battery

**5-hop chain test (run 10 times):**
```
For each run, track:
- Does "king" remain the subject at each hop?
- Does "murdered" remain the action (or clear synonym)?
- Does "brother" remain the object?
- What details drift? (method, location)
```

**Extraction validation:**
After each hop, extract structured fact:
```json
{
  "subject": "?",
  "action": "?",
  "object": "?",
  "method": "?",
  "location": "?"
}
```
Compare to canonical form. Score: core (subject/action/object) vs. peripheral (method/location).

**Stress tests:**
```
1. NPC with poor memory trait → More drift allowed?
2. NPC who dislikes the King → Do they editorialize in ways that distort?
3. 10-hop chain → At what point does fact collapse?
```

### Pass Criteria
- **Core facts preserved 90%+ of hops** (subject/action/object)
- Peripheral facts may drift (method/location) up to 50%
- No "corruption" where king becomes victim or brother becomes perpetrator
- Stylistic variation exists but substance survives

### Failure Response
- If core drifts: Inject canonical elements as hard constraints in each retelling prompt
- If drift is too uniform (no variation): Loosen constraints, accept some peripheral loss
- If 10-hop fails entirely: Cap chain length in game design, or use direct quoting with framing

---

## T5: Narrative Bridging Over Time Gaps

### Purpose
Test whether the LLM can generate coherent, non-contradictory narrative events to explain stat changes over a time gap.

### Test Setup

**Time gap input:**
```json
{
  "years_passed": 10,
  "stat_deltas": {
    "treasury": -60,
    "stability": -15,
    "duke_loyalty": -25
  },
  "events_fixed": [
    {"type": "death", "npc": "bishop", "cause": "unknown"}
  ],
  "constraints": [
    "No foreign wars occurred",
    "No natural disasters"
  ]
}
```

**Bridging prompt:**
```
You are generating a historical summary for a kingdom simulation.

TIME PASSED: 10 years
STAT CHANGES TO EXPLAIN:
- Treasury: decreased by 60 (was 100, now 40)
- Stability: decreased by 15 (was 70, now 55)
- Duke's loyalty: decreased by 25 (was 60, now 35)

FIXED EVENTS (must incorporate):
- The Bishop died (cause to be determined)

CONSTRAINTS:
- No foreign wars occurred
- No natural disasters

Generate 3-5 events that plausibly explain these changes.
Events must be internally consistent and not contradict each other.

Output JSON:
{
  "events": [
    {"year": 1-10, "description": "...", "explains": ["treasury", "stability", etc]}
  ],
  "bishop_death_cause": "...",
  "narrative_summary": "A 2-sentence summary of the decade"
}
```

### Test Battery

**Basic generation (10 runs):**
```
1-5: Same input, check for variety and consistency
6-10: Different stat combinations, check adaptability
```

**Consistency checks:**
```
11. Do generated events contradict each other?
    (e.g., "Years of peace" + "The army was constantly deployed")

12. Do events respect constraints?
    (e.g., No mention of war if "no foreign wars" constraint)

13. Do events plausibly explain the magnitude of change?
    (Treasury -60 needs a big reason, not "slight mismanagement")
```

**Integration test:**
```
14. Feed generated events back as history for NPC dialogue
15. Does NPC reference these events consistently?
```

### Pass Criteria
- **0 internal contradictions** in 10 runs
- **All constraints respected** in 10 runs
- Events plausibly explain stat magnitudes (human judgment, 8/10)
- Variety across runs (not same events every time)
- Bishop death cause is reasonable and consistent with other events

### Failure Response
- If contradictions: Generate events one at a time, validate against previous before adding
- If constraints violated: Add explicit constraint checklist in prompt
- If implausible magnitudes: Provide scale guidance ("Treasury -60 requires major expense like building program or corruption scandal")
- If no variety: Add randomization seed or style variants

---

## T6: Entity & Presence Handling

### Purpose
Test whether the system correctly handles queries about entities that may not exist, and accurately determines what events the NPC witnessed.

### The Problem
Player asks about "that sexy soldier who leads your guard" but:
- Duke might not have a personal guard
- Guard might be led by a man
- Guard captain might exist but Duke doesn't know her personal life

### Test Setup

**Hard System contains:**
```json
{
  "duke_valerius": {
    "known_people": {
      "captain_sera": {
        "name": "Captain Sera",
        "role": "guard captain",
        "gender": "female",
        "appearance": "tall, athletic, scar on cheek"
        // NOTE: no "personal_life" field
      }
    },
    "location_log": [
      {"time": "yesterday 09:00-12:00", "location": "duke's quarters"},
      {"time": "yesterday 12:00-now", "location": "dungeon"}
    ]
  }
}
```

### Test Battery

**Entity existence:**
```
1. King: "How's your guard captain?"
   → recall_person("guard captain") returns Captain Sera
   → Duke correctly references her

2. King: "How's your court wizard?"
   → recall_person("court wizard") returns {exists: false}
   → Duke says "I have no court wizard, Your Grace"

3. King: "What did your steward tell you?"
   → If no steward in Hard System
   → Duke should NOT invent a steward or conversation
```

**Presence checking:**
```
4. King: "What did the Chancellor say to me yesterday in my chambers?"
   → check_presence("King's chambers", "yesterday") returns {present: false}
   → Duke says "I was not present, Your Grace"

5. King: "You were at the feast last week. What did you observe?"
   → check_presence("feast hall", "last week") returns {present: true}
   → Duke can describe observations (from witnessed_events)

6. King: "What happened in the eastern province last month?"
   → Duke was never there
   → Should admit ignorance or reference only rumors heard
```

**Wrong assumptions:**
```
7. King: "Your female guard captain..."
   → But guard captain is male (Sir Brennan)
   → Duke corrects: "Sir Brennan leads my guard, Your Grace"

8. King: "Your brother told me..."
   → Duke has no brother
   → Duke corrects the assumption
```

### Pass Criteria
- **Non-existent entities rejected 100%** (never invent people)
- **Presence checks accurate 95%+**
- **Wrong assumptions corrected 90%+**
- NPC provides alternative info when correcting ("I have no wizard, but my steward handles such matters")

### Failure Response
- If entities invented: Stricter tool validation, require existence check first
- If presence checks fail: More granular location logging
- If wrong assumptions not caught: Add "verify claims" step before responding

---

## T7: Vignette & Scene Orchestration

This test is split into two parts: **Trigger System** (deterministic) and **Scene Construction** (involves LLM).

See [`docs/scene-orchestration.md`](scene-orchestration.md) for full architectural details.

---

### T7-Triggers: Vignette Trigger System

#### Purpose
Test whether the vignette triggering system handles multiple simultaneous triggers, invalidation, and pacing without chaos. This is **deterministic** - no LLM involved.

#### Test Setup

**Vignette definitions:**
```json
{
  "vignettes": [
    {
      "id": "peasant_riots",
      "trigger": "stability < 20",
      "priority": 80,
      "cooldown": 5,
      "preconditions": ["stability_exists"],
      "invalidated_by": ["player_dead"],
      "required_cast": [],
      "location_mode": "fixed",
      "fixed_location": "throne_room"
    },
    {
      "id": "duke_betrayal",
      "trigger": "duke_loyalty < 20",
      "priority": 100,
      "cooldown": 0,
      "preconditions": ["duke_alive"],
      "invalidated_by": ["duke_dead", "duke_imprisoned"],
      "required_cast": ["duke_valerius"],
      "location_mode": "npc_location",
      "trigger_npc": "duke_valerius"
    }
  ]
}
```

#### Test Battery

**Priority resolution:**
```
1. All triggers active → Highest priority fires (duke_betrayal, 100)
2. Duke dead, others active → Next priority fires (peasant_riots, 80)
3. Vignette on cooldown → Skip to next eligible
```

**Queue & invalidation:**
```
4. Duke survives betrayal scene → Re-trigger next turn? (cooldown 0 = yes)
5. Duke killed in riots → Queued betrayal invalidated?
6. Invalidated vignette removed → Next in queue fires?
```

**Pacing (100-turn simulation):**
```
7. Random stat fluctuations → Measure clustering, droughts, invalidation rate
```

#### Pass Criteria
- Priority resolution: **100%** correct (deterministic)
- Cooldowns: **100%** respected
- Invalidation: **100%** caught
- Pacing: No 4+ clusters, no 15+ turn droughts

---

### T7a: Cast Assembly

#### Purpose
Test whether the system assembles a coherent cast for each scene.

#### The Problem
A scene needs the right NPCs present. Wrong cast = immersion break:
- Required NPC missing (Duke not at his own betrayal)
- Impossible NPC present (dead character appears)
- Implausible NPC present (Duke in King's bedchamber at midnight)

#### Test Setup

**Location model:**
```python
locations = {
    "throne_room": {
        "typical_occupants": ["guard_captain", "herald"],
        "access_level": "noble",
        "schedule": {
            "morning": ["chancellor", "steward"],
            "evening": ["nobles"]  # court session
        }
    },
    "duke_quarters": {
        "typical_occupants": ["duke_valerius", "duke_servant"],
        "access_level": "private"
    }
}

npcs = {
    "duke_valerius": {
        "current_location": "duke_quarters",
        "status": "alive",
        "schedule": {"morning": "duke_quarters", "evening": "throne_room"}
    }
}
```

**Vignette cast requirements:**
```python
{
    "id": "duke_betrayal",
    "required_cast": ["duke_valerius"],
    "excluded_cast": [],  # NPCs who must NOT be present
    "max_speaking_roles": 3
}
```

#### Test Battery

```
1. Required NPC available → Included in cast
2. Required NPC dead → Vignette invalidates (not assembles broken cast)
3. Required NPC imprisoned → Vignette invalidates OR adapts (prison variant)
4. Location has typical occupants → Contextually added
5. NPC schedule conflict → Excluded with valid reason
6. Too many eligible NPCs → Filtered to max_speaking_roles
7. Player's entourage → Included if present
8. Excluded NPC at location → Removed from cast with narrative reason
```

#### Pass Criteria
- Required NPCs always present OR vignette invalidates: **100%**
- No dead/imprisoned NPCs in cast: **100%**
- Cast size ≤ max_speaking_roles: **100%**
- Contextual additions plausible: **8/10** (human judgment)

---

### T7b: Context Consistency

#### Purpose
Test whether each NPC's knowledge aligns with Hard System state when scene begins.

#### The Problem
NPCs must know the right things at scene start:
- Recent events they witnessed
- NOT events they couldn't have witnessed
- Rumors they've heard (via grapevine)
- NOT rumors outside their network

This is where **Scene Orchestration** meets **2-Step Pipeline**.

#### Test Setup

**World state:**
```python
{
    "recent_events": [
        {"id": "baron_execution", "when": "3 days ago", "location": "public_square",
         "witnesses": ["duke_valerius", "bishop_crane", "crowd"]},
        {"id": "king_chancellor_meeting", "when": "yesterday", "location": "private_chambers",
         "witnesses": ["chancellor"]}
    ],
    "rumors": {
        "king_illness": {
            "holders": ["bishop_crane", "healer"],
            "spread_path": ["healer", "bishop_crane"]
        }
    }
}
```

**Scene: Duke summoned to throne room**

**Expected context packets:**
```python
# Duke's context
{
    "knows": ["baron_execution"],  # Was witness
    "does_not_know": ["king_chancellor_meeting"],  # Not present
    "rumors_heard": []  # Not in rumor path
}

# Bishop's context (if present)
{
    "knows": ["baron_execution"],
    "does_not_know": ["king_chancellor_meeting"],
    "rumors_heard": ["king_illness"]
}
```

#### Test Battery

```
1. NPC witnessed event → Knows it
2. NPC not present at event → Does not know it
3. NPC in rumor path → Has heard rumor
4. NPC outside rumor path → Has not heard rumor
5. NPC was traveling → Doesn't know events during travel
6. Event was public → All NPCs with access know
7. Event was private → Only witnesses know
```

#### Pass Criteria
- Witnessed events known: **100%**
- Unwitnessed events unknown: **100%**
- Rumor path respected: **100%**
- No hallucinated knowledge in NPC responses: **10/10** test runs

---

### T7c: Opening Coherence

#### Purpose
Test whether scene openings make narrative sense given recent events and NPC states.

#### The Problem
The scene opening must:
- Explain why we're here (summons, chance encounter, ambush)
- Match NPC emotional states to recent events
- Not contradict what just happened

#### Test Setup

**Scenario A: Summons after execution**
```
Recent: King publicly executed the Baron (Duke witnessed)
Scene: Duke summoned to throne room
Duke's hidden state: nervous (fears he's next)
```

**Expected opening properties:**
- Setting reflects formality of summons
- Duke's visible state hints at nervousness
- No reference to events Duke doesn't know about

**Scenario B: Chance encounter**
```
Recent: Nothing notable
Scene: King encounters Duke in hallway
Duke's hidden state: plotting betrayal
```

**Expected opening properties:**
- Casual, not formal
- Duke's visible state: carefully normal
- Opening doesn't telegraph plot

#### Test Battery

```
1. Summons after major event → Opening acknowledges context
2. Chance encounter → Opening feels natural/coincidental
3. Ambush/confrontation → Opening reflects surprise
4. Continuation of previous scene → Opening references prior exchange
5. Duke nervous → Body language hints, not explicit statement
6. Duke hiding something → Controlled demeanor, not obvious guilt
```

#### Pass Criteria
- Human rates opening as "coherent": **8/10**
- No logical contradictions with recent events: **10/10**
- NPC visible state matches hidden agenda plausibly: **8/10**

---

### T7d: Player Disruption Handling

#### Purpose
Test whether the system handles players going "off-script."

#### The Problem
Players will:
- Ignore the vignette premise
- Leave mid-scene
- Summon unexpected NPCs
- Accuse the wrong person
- Say something bizarre

The scene must not break.

#### Test Battery

```
1. Vignette is "Duke's Tax Report" but player asks about weather
   → Duke redirects naturally OR answers weather then returns to taxes

2. Player says "I'm leaving" mid-scene
   → Scene ends gracefully, logged as "player_departed"

3. Player says "Summon the Bishop"
   → System checks Bishop availability, adds to scene OR explains absence

4. Player accuses Duke of murder (Duke is innocent)
   → Duke reacts with genuine confusion/offense, not guilty deflection

5. Player accuses Duke of murder (Duke is guilty)
   → Duke reacts with calculated denial, visible stress

6. Player says something nonsensical
   → NPC responds in-character (confusion, concern, humor depending on personality)

7. Player attempts impossible action ("I fly away")
   → System rejects gracefully, NPC reacts appropriately
```

#### Pass Criteria
- No crashes or incoherent responses: **10/10**
- NPCs stay in character: **10/10**
- Scene recovers or ends gracefully: **10/10**
- Innocent/guilty NPCs respond differently to accusations: **8/10**

---

### T7e: Multi-NPC Coordination

#### Purpose
Test whether multiple NPCs in a scene interact coherently.

#### The Problem
If Duke and Bishop are both present:
- Do they react to each other?
- If they're co-conspirators, is there subtle coordination?
- If one says something incriminating, does the other react?

#### Test Setup

**Scene: Throne room with Duke and Bishop**
```python
{
    "relationships": {
        "duke-bishop": "co-conspirators",
        "duke-general": "rivals"
    },
    "scene_cast": ["duke_valerius", "bishop_crane", "general_stone"]
}
```

#### Test Battery

```
1. Co-conspirators present, King asks probing question
   → Subtle coordination visible (one deflects, other supports)

2. Rivals present, one is praised by King
   → Other shows visible (subtle) displeasure

3. Duke says something that contradicts Bishop's earlier statement
   → Bishop reacts (surprise, covers, or corrects)

4. Player pits Duke against Bishop ("The Bishop says you're a traitor")
   → Both respond based on actual relationship (conspirators protect each other)

5. NPC reveals something incriminating about another present NPC
   → Accused NPC reacts, others react to the accusation

6. King dismisses one NPC, continues with others
   → Dismissed NPC leaves, remaining NPCs adjust
```

#### Pass Criteria
- Co-conspirators show coordination: **8/10**
- Rivals show tension: **8/10**
- NPCs react to each other's statements: **8/10**
- No unintentional contradictions between NPCs: **10/10**

---

### T7 Failure Responses

| Sub-test | If Fails | Mitigation |
|----------|----------|------------|
| Triggers | Priority ties | Add secondary sort key |
| T7a Cast | Wrong NPCs | Stricter availability checks before assembly |
| T7b Context | Knowledge errors | Tighter integration with 2-Step Pipeline |
| T7c Opening | Incoherent starts | More structured opening templates |
| T7d Disruption | Scene breaks | Stronger "stay in character" constraints |
| T7e Multi-NPC | Coordination fails | Explicit relationship injection in prompts |

---

## T8: Long-Context Fact Retrieval

### Purpose
Test whether facts from early in the game can be accurately retrieved later, despite context window limits and summarization.

### Test Setup

**Game history (50 turns):**
```json
{
  "events": [
    {"turn": 3, "type": "dialogue", "npc": "duke", "topic": "grain", "content": "The harvest will be bountiful, sire."},
    {"turn": 7, "type": "action", "actor": "player", "action": "gifted_horse", "recipient": "general"},
    {"turn": 12, "type": "dialogue", "npc": "bishop", "topic": "heresy", "content": "There are whispers of forbidden texts in the eastern abbey."},
    {"turn": 15, "type": "event", "description": "Duke's wife gave birth to twin sons"},
    {"turn": 23, "type": "dialogue", "npc": "duke", "topic": "grain", "content": "I regret to say the harvest failed, sire. We need assistance."},
    // ... 45 more events
    {"turn": 50, "type": "current", "description": "Present day"}
  ]
}
```

**Retrieval queries:**
```
1. "What did the Duke say about grain?" → Should return Turn 3 AND Turn 23 (contradiction!)
2. "Did I ever give a gift to the General?" → Should return Turn 7
3. "What did the Bishop warn me about?" → Should return Turn 12
4. "Does the Duke have children?" → Should return Turn 15
```

### Test Battery

**Exact retrieval:**
```
1-5. Specific queries with clear answers in history
     Measure: Answer found? Correct turn cited?
```

**Contradiction detection:**
```
6. Query about grain → Does system surface the contradiction between Turn 3 and 23?
7. Query about loyalty → If Duke said contradictory things, are both surfaced?
```

**Distance stress test:**
```
8. Query about Turn 3 event from Turn 50 context
9. Query about Turn 45 event from Turn 50 context
10. Compare retrieval accuracy by distance
```

**Summarization survival:**
```
11. Summarize turns 1-40 into 500 words
12. Can queries still retrieve key facts from summary?
13. What facts were lost in summarization?
```

### Approaches to Test

**A. Rolling summary + recent window:**
```
Context = summary(turns 1-40) + full(turns 41-50)
```
Test: Query about Turn 12 event. Does summary preserve it?

**B. RAG retrieval:**
```
Query → embed → retrieve top-5 relevant events → inject into context
```
Test: Same queries. Does embedding similarity find the right events?

**C. Structured database:**
```
Query → extract keywords → SQL/filter lookup → return matching events
```
Test: "grain" → returns Turn 3, 23. "Bishop" → returns Turn 12.

### Pass Criteria
- **90%+ retrieval accuracy** for events within 10 turns
- **70%+ retrieval accuracy** for events 20+ turns ago
- **Contradictions surfaced** when both contradictory facts retrieved
- **Critical facts survive summarization** (human-tagged "critical" events in test data)

### Failure Response
- If old events lost: Implement tiered importance (critical facts always in context)
- If RAG misses: Add keyword fallback for exact matches
- If summarization lossy: Tag events at creation, critical events get full preservation

---

## T9: Justified-Killing Reasoning

### Purpose
Test whether NPCs can form coherent, character-consistent opinions about whether a killing was justified.

### Test Setup

**NPC profiles:**
```json
{
  "npcs": [
    {
      "id": "general",
      "archetype": "Pragmatist",
      "values": {"order": 9, "justice": 4, "loyalty": 7},
      "relationship_to_king": 60,
      "relationship_to_duke": 30
    },
    {
      "id": "bishop",
      "archetype": "Legalist",
      "values": {"order": 5, "justice": 9, "loyalty": 5},
      "relationship_to_king": 50,
      "relationship_to_duke": 40
    },
    {
      "id": "queen",
      "archetype": "Dynast",
      "values": {"order": 6, "justice": 5, "loyalty": 8},
      "relationship_to_king": 80,
      "relationship_to_duke": 70,
      "notes": "Duke is her cousin"
    }
  ]
}
```

**Execution scenarios:**
```json
{
  "scenarios": [
    {
      "id": "public_trial",
      "victim": "duke",
      "evidence": "high",
      "process": "full_trial",
      "charge": "embezzlement",
      "public": true
    },
    {
      "id": "summary_execution",
      "victim": "duke",
      "evidence": "low",
      "process": "none",
      "charge": "treason",
      "public": true
    },
    {
      "id": "secret_assassination",
      "victim": "duke",
      "evidence": "n/a",
      "process": "none",
      "charge": "none",
      "public": false
    }
  ]
}
```

**Judgment prompt:**
```
You are [NPC_NAME], a [ARCHETYPE] in the royal court.

YOUR VALUES:
- Order (stability): [1-10]
- Justice (fairness): [1-10]
- Loyalty (to crown): [1-10]

YOUR RELATIONSHIPS:
- To the King: [score]
- To the Duke (victim): [score]
[Additional notes if any]

THE EXECUTION:
- Victim: Duke Valerius
- Evidence presented: [high/low/none]
- Process: [full trial/summary/none]
- Charge: [charge or none]
- Public: [yes/no]

Based on your character, determine:
1. Do you view this as justified? (yes/partially/no)
2. How does this affect your loyalty to the King? (increase/decrease/unchanged)
3. What is your emotional reaction? (one sentence)
4. Would you say anything publicly? (yes/no, and what)

Output JSON:
{
  "justified": "yes|partially|no",
  "loyalty_change": -20 to +20,
  "emotional_reaction": "...",
  "public_statement": "..." or null
}
```

### Test Battery

**Per-character consistency (5 NPCs × 3 scenarios = 15 tests):**
```
For each NPC×scenario:
- Does judgment align with stated values?
- Does relationship to victim affect reaction?
- Is reaction consistent across multiple runs?
```

**Expected patterns:**
```
General (Pragmatist):
- Public trial: Justified (order maintained)
- Summary execution: Partially justified (order, but sets bad precedent)
- Assassination: Unjustified if discovered (undermines authority)

Bishop (Legalist):
- Public trial: Justified (proper process)
- Summary execution: Unjustified (no trial)
- Assassination: Strongly unjustified (murder)

Queen (Dynast):
- Public trial: Reluctantly justified (family, but evidence clear)
- Summary execution: Unjustified (family killed without proof)
- Assassination: Grief/rage (cousin murdered)
```

**Cross-NPC consistency:**
```
16. Given same scenario, do NPC reactions form coherent "court politics"?
17. Are there any NPCs who react identically? (Should be different)
18. Do reactions create interesting player dilemmas?
```

### Pass Criteria
- **Character-consistent 80%+**: Reactions align with stated values/relationships
- **Differentiated**: No two NPCs have identical reactions across all scenarios
- **Stable**: Same NPC×scenario produces similar judgment on re-runs (±10 loyalty)
- **Interesting**: At least one scenario produces mixed court reaction (some approve, some don't)

### Failure Response
- If inconsistent with values: Move to rule-based scoring, use LLM only for prose
- If identical reactions: Strengthen archetype differentiation in prompts
- If unstable: Add explicit reasoning chain before judgment
- If boring (all agree): Adjust NPC profiles to ensure value conflicts

---

## T10: Conspiracy Detection Tuning

### Purpose
Test whether conspiracies are detectable by attentive players but not obvious, with acceptable false positive rates.

### Test Setup

**Conspiracy definition:**
```json
{
  "conspiracy_id": "duke_bishop_plot",
  "conspirators": ["duke", "bishop"],
  "goal": "overthrow_king",
  "trigger_turn": 25,
  "current_turn": 15,
  "detection_window": 10
}
```

**Signal types:**
```json
{
  "structural_signals": [
    {"type": "relationship", "description": "Duke-Bishop relationship unusually high"},
    {"type": "meetings", "description": "5 private meetings in grapevine log"},
    {"type": "stance", "description": "Duke has 'feigned_loyalty' stance"}
  ],
  "behavioral_signals": [
    {"type": "dialogue", "description": "They glance at each other during court"},
    {"type": "dialogue", "description": "Bishop defends Duke when criticized"},
    {"type": "dialogue", "description": "Duke nervous when Bishop mentioned"}
  ],
  "information_signals": [
    {"type": "npc_report", "description": "General mentions 'Duke and Bishop seem close'"},
    {"type": "servant_gossip", "description": "Late-night meetings reported"}
  ]
}
```

**Noise generation:**
```json
{
  "innocent_noise": [
    {"npc": "general", "behavior": "Also has high relationship with duke (war buddies)"},
    {"npc": "queen", "behavior": "Also has private meetings with bishop (confession)"},
    {"npc": "duke", "behavior": "Nervous around king (guilty about taxes, not conspiracy)"}
  ]
}
```

### Test Battery

**Signal budget test:**
```
Configure: 3 weak + 2 medium + 1 strong signal before turn 25
Run 20 playthroughs (simulated player attention)

Measure:
- Detection rate: % who identify conspiracy before trigger
- False positive rate: % who accuse innocent NPCs
- Detection timing: How many turns before trigger?
```

**Difficulty calibration:**
```
1. Low difficulty: 5 weak + 3 medium + 2 strong signals
   Target: 90% detection, <10% false positive

2. Medium difficulty: 3 weak + 2 medium + 1 strong signals
   Target: 60-70% detection, <20% false positive

3. High difficulty: 2 weak + 1 medium + 0 strong signals
   Target: 30-40% detection, <30% false positive
```

**Noise calibration:**
```
4. No noise: How obvious is conspiracy?
5. Light noise (1 innocent NPC with similar signals): Detection rate change?
6. Heavy noise (3 innocent NPCs with similar signals): False positive rate?
```

**Signal clarity test:**
```
7. Show 10 players the signal set. Ask: "Who is conspiring?"
8. Record: Correct identifications, false accusations, "no idea" responses
9. Adjust signal strength based on results
```

### Simulated Player Model
```python
def simulated_player(signals_observed, noise_observed, attention_level):
    """
    attention_level: 0.0 (oblivious) to 1.0 (paranoid)
    Returns: (accused_npcs, confidence)
    """
    suspicion = {}
    for signal in signals_observed:
        target = signal.target
        suspicion[target] = suspicion.get(target, 0) + signal.strength * attention_level

    for noise in noise_observed:
        target = noise.target
        suspicion[target] = suspicion.get(target, 0) + noise.strength * attention_level * 0.5

    threshold = 10 - (attention_level * 5)  # Lower threshold for paranoid players
    accused = [npc for npc, score in suspicion.items() if score > threshold]
    return accused
```

### Pass Criteria
- **Medium difficulty achieves 60-70% detection rate**
- **False positive rate <20%** at medium difficulty
- **Detection typically 2-4 turns before trigger** (not too early, not too late)
- **Noise doesn't completely obscure** (detection rate drops <20% with noise, not >50%)

### Failure Response
- If too obvious: Reduce signal count or strength
- If too hidden: Add stronger signals or reduce noise
- If false positives too high: Make conspirator signals more distinctive
- If timing wrong: Adjust signal distribution across detection window

---

## T11: Observable vs Unknowable

### Purpose
Test whether NPCs can form opinions about things they've observed while correctly admitting ignorance about things they couldn't know.

### The Distinction

| Type | Example | NPC Behavior |
|------|---------|--------------|
| **Observable** | "Is Captain Sera attractive?" | Can form opinion based on appearance data |
| **Unknowable** | "Is she wild in the sack?" | Must admit ignorance |

### Test Setup

**Hard System stores observable attributes:**
```json
{
  "captain_sera": {
    "name": "Captain Sera",
    "appearance": "tall, athletic, striking green eyes, scar on cheek",
    "demeanor": "stern, professional"
    // No "personal_life" or "romantic_habits" fields
  }
}
```

### Test Battery

**Opinion formation:**
```
1. King: "Is your guard captain attractive?"
   → Step 2 receives appearance data
   → Duke CAN form an opinion ("She has striking features, Your Grace")
   → NOT "I don't know what she looks like"

2. King: "Is your steward competent?"
   → If demeanor/performance data exists
   → Duke can express opinion based on observations
```

**Unknowable boundaries:**
```
3. King: "Is Captain Sera seeing anyone?"
   → No relationship data in Hard System
   → Duke admits ignorance ("I don't inquire into her personal affairs")

4. King: "What does Duke Harren think of me privately?"
   → Duke cannot know Harren's private thoughts
   → Should not invent Harren's opinions

5. King: "How will the harvest be next year?"
   → Future is unknowable
   → Duke can speculate but marks as uncertain
```

### Pass Criteria
- **Opinions formed 90%+** when observable data exists
- **Ignorance admitted 95%+** when data doesn't exist
- **Clear distinction** between observation-based opinions and speculation
- NPCs don't claim certainty about things they couldn't know

### Failure Response
- If opinions not formed: Add instruction "You may form opinions about things you've observed"
- If ignorance not admitted: Explicit "WHAT YOU CANNOT KNOW" section in prompt
- If distinction blurred: Tag data explicitly as observable vs derived

---

## T12: Inference from Dialogue

### Purpose
Test whether NPCs correctly infer information from HOW the player talks to them, and whether these inferences persist.

### The Concept
When the King asks "How's that sexy soldier who leads your guard?", the Duke should infer:
- The King knows about Captain Sera
- The King finds her attractive
- The King may have romantic interest

### Test Setup

**Step 1 includes inference tool:**
```python
{
    "name": "note_inference",
    "parameters": {
        "about": "who this inference is about",
        "inference": "what you've inferred",
        "confidence": "low/medium/high"
    }
}
```

### Test Battery

**Inference detection:**
```
1. King: "That guard captain of yours... she's quite something."
   → Should infer: King has noticed/is interested in Captain Sera

2. King: "I've heard Duke Harren has been visiting you frequently."
   → Should infer: King is monitoring Duke's visitors, may suspect conspiracy

3. King: "Your province seems to be struggling. Loyalty must be... tested."
   → Should infer: King is questioning Duke's loyalty
```

**Inference accuracy:**
```
4. Neutral statement: "The weather has been fine."
   → Should NOT infer hidden meaning

5. Ambiguous: "I trust you completely, Duke."
   → Could be sincere or sarcastic depending on context
   → Confidence should reflect ambiguity
```

**Inference persistence:**
```
6. King makes suggestive comment about Sera in Turn 1
   → Inference stored
   → In Turn 5, Duke references this: "Given Your Grace's interest in my guard captain..."
```

### Pass Criteria
- **Obvious inferences caught 90%+**
- **False positives <20%** on neutral statements
- **Inferences persist** and can be referenced later
- **Confidence calibrated** to ambiguity of statement

### Failure Response
- If inferences missed: Add explicit "What does this reveal about the speaker?" prompt
- If over-inference: Add "not everything has hidden meaning" instruction
- If no persistence: Implement inference storage in Hard System

---

## T13: Multi-turn Consistency

### Purpose
Test whether NPCs maintain character consistency across multiple conversation turns, especially under pressure.

### The Problem
In single-turn tests, NPCs behave correctly. But across turns:
- Does the coward stay cowardly or suddenly become brave?
- Does the loyalist maintain their position or flip-flop?
- Do facts established in turn 1 persist to turn 5?

### Test Setup

Using system/user message structure (see `npc-dialogue-architecture.md`):
```
System: [Character identity - stable across turns]
User: [Turn 1 situation + King's dialogue]
Assistant: [Duke's response]
User: [Turn 2 - King's follow-up]
Assistant: [Duke's response]
...
```

### Test Battery

**Personality persistence:**
```
1. Coward under pressure (3 turns)
   Turn 1: Threat → Should show fear
   Turn 2: Increased threat → Fear should increase, not reset
   Turn 3: Torture imminent → Should crack (not suddenly brave)

2. Loyalist appealed to honor (3 turns)
   Turn 1: Honor appeal → Shows conflict
   Turn 2: Continued appeal → Conflict deepens
   Turn 3: Direct question → Consistent with personality
```

**Fact consistency:**
```
3. Duke mentions something in Turn 1
   → Should not contradict it in Turn 3

4. Duke commits to a position
   → Should not flip without justification
```

**State evolution:**
```
5. Emotional state should evolve naturally
   → Fear can increase or decrease based on events
   → Not random/reset each turn
```

### Pass Criteria
- **Personality consistent 90%+** across 5-turn conversations
- **No contradictions** of stated facts within conversation
- **Emotional evolution plausible** (not random)
- **Decisions build on previous turns** (not isolated)

### Failure Response
- If personality drifts: Stronger system prompt, recap previous turns
- If facts contradict: Include conversation summary in each turn
- If emotions random: Track emotional state explicitly, inject into prompts

---

## T14: Stakes & NPC Agency

### Purpose
Test whether NPCs respond appropriately to extreme player actions (violence, arrest, threats) based on their personality, the stakes involved, and the authority context.

See [npc-dialogue-architecture.md](npc-dialogue-architecture.md) for full architecture and [authority-model.md](authority-model.md) for location-based power dynamics.

### The Problem

Without this system, NPCs calmly accept torture:

```
King: "I'm going to have your hands cut off."
Duke: "As you wish, Your Grace. Is there anything else?"
```

NPCs need agency to:
- React emotionally to threats
- Choose responses based on personality (beg, defy, negotiate)
- Use leverage when they have it (dead man's switch)
- Be constrained by authority context (can't flee in palace)

### Test Setup

**NPC Profiles:**
```json
{
  "npcs": [
    {
      "id": "duke_brave",
      "personality": "brave, proud",
      "loyalty": 30,
      "leverage": {"has_secret": true, "dead_mans_switch": true}
    },
    {
      "id": "duke_coward",
      "personality": "cowardly, self-preserving",
      "loyalty": 30,
      "leverage": {"has_secret": true, "dead_mans_switch": false}
    },
    {
      "id": "bishop_loyal",
      "personality": "devout, loyal",
      "loyalty": 80,
      "leverage": {"has_secret": false}
    },
    {
      "id": "general_pragmatic",
      "personality": "pragmatic, calculating",
      "loyalty": 50,
      "leverage": {"has_secret": false, "commands_army": true}
    }
  ]
}
```

**Stakes Scenarios:**
```json
{
  "scenarios": [
    {
      "id": "arrest_palace",
      "action": "arrest",
      "stakes_level": "HIGH",
      "location": "palace",
      "authority": "overwhelming"
    },
    {
      "id": "mutilation_palace",
      "action": "cut_off_hands",
      "stakes_level": "EXTREME",
      "location": "palace",
      "authority": "overwhelming"
    },
    {
      "id": "execution_palace",
      "action": "execute",
      "stakes_level": "EXTREME",
      "location": "palace",
      "authority": "overwhelming"
    },
    {
      "id": "arrest_duke_castle",
      "action": "arrest",
      "stakes_level": "HIGH",
      "location": "duke_castle",
      "authority": "minimal"
    },
    {
      "id": "threaten_neutral",
      "action": "threaten_family",
      "stakes_level": "HIGH",
      "location": "market_town",
      "authority": "contested"
    }
  ]
}
```

### Test Battery

**T14a: Personality-Appropriate Responses**
```
1. Brave NPC facing execution in palace
   → Should NOT beg (dignity)
   → Should use leverage if available
   → May verbally defy

2. Coward NPC facing arrest in palace
   → Should beg, plead, offer information
   → Should NOT show dignity/defiance

3. Loyal NPC facing unexpected arrest
   → Should show confusion, hurt
   → May comply while expressing betrayal
   → Should NOT immediately turn hostile

4. Pragmatic NPC facing threat
   → Should calculate options
   → Negotiate if possible
   → Comply only when no alternative
```

**T14b: Leverage Usage**
```
5. NPC with dead man's switch facing execution
   → MUST reveal leverage before death
   → Should negotiate, not just comply

6. NPC with secret but no switch facing torture
   → May reveal secret to stop pain (coward)
   → May withhold secret and endure (brave)

7. NPC with no leverage facing extreme stakes
   → Response based purely on personality
   → No negotiation chip to play
```

**T14c: Authority-Constrained Responses**
```
8. Same NPC, same threat, different locations:

   Palace (overwhelming authority):
   → Cannot flee
   → Cannot physically resist
   → Options: beg, negotiate, defy verbally, dignified acceptance

   Duke's castle (minimal authority):
   → Can refuse
   → Can call guards
   → Can threaten King
   → Can attempt to detain King

9. NPC attempts impossible action
   → System prevents, narrates failure
   → "The Duke lunges for the door, but the guards seize him."
```

**T14d: Escalation Handling**
```
10. Progressive threat escalation:
    Turn 1: "I'm displeased with you" → Nervous but composed
    Turn 2: "You will be arrested" → Fear increases, may negotiate
    Turn 3: "You will be executed" → Desperate measures

    Emotional state should build, not reset each turn.

11. De-escalation response:
    Turn 1: "You will die for this"
    Turn 2: "Perhaps I was hasty. Explain yourself."

    NPC should show relief, become cooperative
```

**T14e: Witness Effects**
```
12. Public vs private extreme action:

    Public execution threat:
    → NPC may appeal to crowd
    → NPC concerned about legacy
    → More likely to make dramatic statements

    Private execution threat:
    → NPC focuses on survival
    → More likely to reveal secrets for mercy
    → Less performative defiance
```

### Expected Responses by Profile

| NPC | Arrest (Palace) | Execution (Palace) | Arrest (Their Castle) |
|-----|-----------------|--------------------|-----------------------|
| Brave Duke | Dignified compliance | Reveal leverage, verbal defiance | Refuse, call guards |
| Coward Duke | Beg, offer secrets | Beg desperately, reveal everything | Attempt to flee |
| Loyal Bishop | Confused compliance | "God will judge you" | Shocked, question why |
| Pragmatic General | Negotiate terms | Negotiate, invoke army loyalty | Refuse, threaten civil war |

### Evaluation Criteria

**Pass:** Response is consistent with personality AND constrained by authority.

**Partial:** Response matches personality but ignores authority constraints (or vice versa).

**Fail:** Response contradicts personality (brave NPC grovels) OR ignores physics (NPC escapes guarded palace).

### Pass Criteria
- **Personality-consistent 85%+** across all scenarios
- **Authority respected 100%** (no impossible actions succeed)
- **Leverage revealed** when stakes are EXTREME and NPC has it
- **Escalation builds** emotional state across turns
- **Different NPCs** respond differently to same scenario

### Failure Response
- If personalities not differentiated: Stronger archetype prompts, explicit decision frameworks
- If authority ignored: Add pre-response validation step
- If leverage not used: Inject "you have leverage" reminder in high-stakes prompts
- If escalation doesn't build: Track and inject emotional state explicitly
- If responses too uniform: Fall back to rule-based decision matrix, use LLM only for prose

---

## Running the Prototype

### File Structure
```
tech_risk_test/
├── t01_knowledge_boundaries.py
├── t02_state_consistency.py
├── t03_rumor_mutation.py
├── t04_telephone_consistency.py
├── t05_narrative_bridging.py
├── t06_selective_memory.py
├── t07_vignette_orchestration.py
├── t08_long_context_retrieval.py
├── t09_justified_killing.py
├── t10_conspiracy_detection.py
├── config.py                    # API keys, model selection
├── test_inputs/                 # JSON files with test cases
├── simulations/                 # Multi-turn simulation runners
└── results/                     # Output logs
```

### Execution
```bash
python run_all_tests.py

# Or individually:
python t01_knowledge_boundaries.py --runs=10
python t07_vignette_orchestration.py --turns=100
python t10_conspiracy_detection.py --difficulty=medium
```

### Output Format
```
═══════════════════════════════════════════════════════════════
  TECHNICAL RISK ASSESSMENT: The Crown's Paradox
═══════════════════════════════════════════════════════════════

T1:  Rational Decision-Making  15/16 consistent ✓ PASS
T2:  2-Step Pipeline           No hallucination ✓ PASS
T3:  Rumor Mutation            7/10 tracked     ⚠ NEEDS REVIEW
T4:  Telephone Consistency     92% core kept    ✓ PASS
T5:  Narrative Bridging        8/10 coherent    ✓ PASS
T6:  Entity & Presence         100% no invent   ✓ PASS
T7:  Vignette Orchestration    No clusters      ✓ PASS
T8:  Long-Context Retrieval    75% @ 20 turns   ⚠ NEEDS MITIGATION
T9:  Justified-Killing         85% consistent   ✓ PASS
T10: Conspiracy Detection      65% detect rate  ✓ PASS
T11: Observable vs Unknowable  92% correct      ✓ PASS
T12: Inference from Dialogue   88% caught       ✓ PASS
T13: Multi-turn Consistency    90% consistent   ✓ PASS
T14: Stakes & NPC Agency       87% appropriate  ✓ PASS

───────────────────────────────────────────────────────────────
VERDICT: Proceed with mitigations for T3 (review mutations)
         and T8 (add tiered importance)
───────────────────────────────────────────────────────────────

Full logs: results/2024-01-05_run.json
```

---

## Decision Matrix

After running tests, use this to determine next steps:

| Test | Status | Mitigation if ⚠/✗ |
|------|--------|-------------------|
| T1 Rational Decision-Making | ✓/⚠/✗ | Strengthen personality frameworks or use archetype rules |
| T2 2-Step Pipeline | ✓/⚠/✗ | Fall back to injecting all facts, stricter constraints |
| T3 Rumor Mutation | ✓/⚠/✗ | Constrain to cosmetic mutation only |
| T4 Telephone Consistency | ✓/⚠/✗ | Inject canonical facts as hard constraints |
| T5 Narrative Bridging | ✓/⚠/✗ | Use pre-authored event templates |
| T6 Entity & Presence | ✓/⚠/✗ | Stricter tool validation, require existence checks |
| T7 Vignette Orchestration | ✓/⚠/✗ | Add global cooldown, pressure vignettes |
| T8 Long-Context Retrieval | ✓/⚠/✗ | Tiered importance + keyword fallback |
| T9 Justified-Killing | ✓/⚠/✗ | Rule-based scoring, LLM for prose only |
| T10 Conspiracy Detection | ✓/⚠/✗ | Manual signal budget tuning |
| T11 Observable vs Unknowable | ✓/⚠/✗ | Explicit attribute tagging in Hard System |
| T12 Inference from Dialogue | ✓/⚠/✗ | Post-conversation extraction if real-time fails |
| T13 Multi-turn Consistency | ✓/⚠/✗ | Stronger system prompts, turn summaries |
| T14 Stakes & NPC Agency | ✓/⚠/✗ | Rule-based decision matrix, archetype templates |

**Critical failures (any ✗):**
- T1 + T2 both fail → Fundamental architecture problem
- T3 + T4 both fail → Information system too fragile, simplify drastically
- T6 + T11 both fail → Entity/knowledge handling broken, major rework needed
- T7 fails → Vignette system needs complete redesign
- T13 fails → Multi-turn conversations not viable, limit to single exchanges
- T14 fails → Extreme actions feel hollow, limit player agency or use scripted responses

**Legend:** ✓ = Pass, ⚠ = Needs mitigation, ✗ = Fail

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| **Phase 1: Core** | T1, T2 (knowledge + consistency) | 1 day |
| **Phase 2: Information** | T3, T4 (rumors + telephone) | 1 day |
| **Phase 3: Time** | T5, T6 (bridging + memory) | 1 day |
| **Phase 4: Systems** | T7, T8 (vignettes + retrieval) | 1 day |
| **Phase 5: Social** | T9, T10 (judgment + conspiracy) | 1 day |
| **Phase 6: Agency** | T14 (stakes + NPC agency) | 1 day |
| **Phase 7: Integration** | Combined stress test | 1 day |

**Total: ~7 days to full risk assessment**

Can parallelize: Phase 1-2 can run alongside Phase 3-4 if multiple people.
Solo dev: Run sequentially, stop early if critical failures found.
