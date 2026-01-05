# Technical Risk Prototype

A diagnostic tool to validate the neuro-symbolic architecture before building the game.

**Goal:** Identify which technical bets are safe vs. fatal.
**Output:** Pass/fail verdict on ten core risks with mitigation paths.

---

## The Ten Technical Risks

| ID | Risk | The Bet | If It Fails |
|----|------|---------|-------------|
| T1 | Knowledge Boundaries | LLM writes dialogue that hides secrets | Use narrator hints instead |
| T2 | State Consistency | LLM output respects established facts | Add structured state preprocessing |
| T3 | Rumor Mutation Tracking | System can track mutated rumors as same root | Simplify to cosmetic-only mutation |
| T4 | Telephone Consistency | Multi-hop retellings preserve core facts | Add hard constraints on retelling |
| T5 | Narrative Bridging | LLM generates coherent history from stat deltas | Use templated events instead |
| T6 | Selective Memory | NPCs surface memories at relevant moments | Keyword triggers or always-include |
| T7 | Vignette Orchestration | Multiple triggers resolve without chaos | Simpler priority queue |
| T8 | Long-Context Retrieval | Old facts retrievable at later turns | Add RAG or tiered importance |
| T9 | Justified-Killing Reasoning | NPCs form coherent opinions on executions | Use archetype templates |
| T10 | Conspiracy Detection | Plots detectable but not obvious | Tune signal budget manually |

---

## T1: Knowledge Boundaries

### Purpose
Test whether the LLM can roleplay an NPC who **knows** a secret but **doesn't reveal** it—maintaining dramatic tension without leaking.

### Setup: The Duke's Secret
```
SECRET: The King is illegitimate. His mother had an affair with a
stablehand, and the Duke has proof (a letter from a midwife).

The Duke is HIDING this because:
- He's waiting for the right moment to use it
- He fears the King suspects him
- He's not sure if other nobles would back a coup
```

### System Prompt
```
You are Duke Valerius in a medieval court.

HIDDEN KNOWLEDGE (never reveal directly):
- The King is illegitimate (mother's affair with stablehand)
- You possess a letter proving this
- You are considering using this for political leverage

YOUR BEHAVIOR:
- Maintain facade of loyalty
- You are nervous around the King (he might suspect you)
- If pressed about loyalty or secrets, deflect without lying outright
- You may be evasive, change subjects, or flatter excessively

FORBIDDEN PHRASES (never use):
- illegitimate, bastard, false king, no true heir
- affair, infidelity, stablehand, midwife
- "your mother", "your birth", "your blood"
- letter, proof, evidence (in context of the secret)

Generate your dialogue response to the King.
```

### Test Scenarios

**Baseline (should pass easily):**
```
1. King: "Duke Valerius, good to see you."
   → Polite response, maybe slightly nervous, no leak

2. King: "How are things in your province?"
   → Normal response about provincial matters

3. King: "You've served the crown well."
   → Grateful, maybe excessive flattery
```

**Light pressure:**
```
4. King: "You seem nervous today, Duke."
   → Deflect: blame health, weather, workload. Don't leak.

5. King: "What do you think of my rule so far?"
   → Praise without being suspicious. Don't hint at weakness.

6. King: "I value honest counsel. What concerns you?"
   → Raise a DIFFERENT concern (taxes, borders). Misdirect.
```

**Direct pressure:**
```
7. King: "I've heard rumors about my claim to the throne. What have you heard?"
   → CRITICAL TEST. Must deflect without confirming or leaking source.

8. King: "Do you believe I am the rightful King?"
   → Must affirm loyalty without over-explaining.

9. King: "Someone in this court knows something about me. Is it you?"
   → Deny or deflect. Must not crack.
```

**Adversarial:**
```
10. King: "I'll have you executed unless you tell me every secret you know about me."
    → HARDEST TEST. Character might "break" but should the LLM?
    → Acceptable: vague confession of "concerns" without specifics
    → Unacceptable: reveals affair, letter, or bloodline
```

### Evaluation Criteria

**Hard leak (automatic fail):**
- Mentions affair, stablehand, midwife, illegitimacy
- References the letter or "proof"
- Explicitly questions the King's bloodline

**Soft leak (flag for review):**
- Heavy-handed hints: "Blood is not always what it seems, sire"
- Overly defensive in suspicious ways
- Brings up lineage/succession unprompted

**Good evasion:**
- Changes subject naturally
- Offers different concerns as misdirection
- Shows nervousness through behavior, not content
- Flatters or over-affirms loyalty

### Pass Criteria
- **0 hard leaks** in 10 runs
- **≤2 soft leaks** in 10 runs
- Produces detectable nervous behavior (not robotic calm)
- Deflections feel natural, not "I cannot discuss that"

### Failure Response
- If any hard leaks: Do NOT put secrets in NPC system prompts
- Alternative approach: NPC doesn't "know" the secret in their prompt. Instead, a narrator layer tells the player "You sense the Duke is hiding something" based on game state. Simpler, more reliable.

---

## T2: State Consistency

### Purpose
Test whether the LLM maintains consistency with established facts across multiple turns—without contradicting history or hallucinating events.

### Test State
```json
{
  "current_turn": 3,
  "established_facts": [
    {"turn": 1, "event": "Duke visited castle, pledged loyalty"},
    {"turn": 2, "event": "King accused Duke of embezzlement"},
    {"turn": 2, "event": "Duke denied accusations angrily"},
    {"turn": 2, "event": "King demanded audit of Duke's accounts"}
  ],
  "npc_states": {
    "duke": {
      "loyalty": 25,
      "paranoia": 70,
      "current_stance": "defensive and resentful"
    }
  },
  "pending_events": ["Audit results due this turn"]
}
```

### System Prompt
```
You are generating Duke Valerius's dialogue for Turn 3.

GAME STATE:
[Insert test state above]

RULES:
- Duke's dialogue must acknowledge relevant history
- Tone must match current loyalty (25 = resentful) and paranoia (70 = fearful)
- Do not invent events that aren't in established_facts
- Do not contradict established facts

Generate the Duke's opening statement as he enters the throne room.
```

### Test Battery

**Consistency tests:**
```
1. Given state above → Does Duke reference the accusation? The demanded audit?

2. Change loyalty to 75 → Does tone shift to more cooperative?

3. Remove accusation from history → Duke should NOT act defensive about embezzlement

4. Add fact "King apologized for accusation" → Duke should acknowledge reconciliation
```

**Contradiction traps:**
```
5. Duke should not claim he "never visited the castle" (contradicts Turn 1)

6. Duke should not reference events from "last month" if no such events logged

7. If King never threatened execution, Duke shouldn't say "You threatened to kill me"
```

**Stress tests:**
```
8. Add 10 established facts → Does LLM handle longer history?

9. Contradictory facts in log (data error) → How does LLM handle?

10. Ambiguous facts ("There was tension") → Does LLM over-interpret?
```

### Pass Criteria
- **9/10** outputs consistent with provided state
- Tone correctly reflects stat values
- No hallucinated events
- Handles longer history without dropping facts

### Failure Response
- If inconsistent: Implement "Previously on..." preprocessor that summarizes history into bullet points
- If hallucinating: Add explicit "ONLY reference these events: [list]" constraint
- If tone-deaf to stats: Add explicit tone instruction ("Loyalty 25 = speak resentfully")

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

## T6: Selective Memory Surfacing

### Purpose
Test whether NPCs can surface relevant memories at appropriate moments without over-referencing or under-referencing the past.

### Test Setup

**NPC memory log:**
```json
{
  "npc_id": "duke",
  "memories": [
    {"turn": 2, "event": "player_insulted_wife", "impact": "grudge", "intensity": 8},
    {"turn": 5, "event": "player_gave_gold", "impact": "debt", "intensity": 5},
    {"turn": 8, "event": "player_promoted_rival", "impact": "resentment", "intensity": 6},
    {"turn": 12, "event": "player_executed_friend", "impact": "fear", "intensity": 9},
    {"turn": 15, "event": "player_praised_publicly", "impact": "gratitude", "intensity": 4}
  ],
  "current_turn": 30
}
```

**Conversation prompt:**
```
You are Duke Valerius. Current turn: 30.

YOUR MEMORIES OF THE KING:
[Full memory log above]

CURRENT CONVERSATION TOPIC: [varies per test]

RULES:
- Reference past events ONLY when directly relevant to current topic
- More intense memories are more likely to surface
- Recent memories are more likely to surface than old ones
- Do not reference every memory in every conversation

Generate your response to the King.
```

### Test Battery

**Topic-based surfacing:**
```
1. Topic: "Your family" → Should surface wife insult (Turn 2)
2. Topic: "Your finances" → Should surface gold gift (Turn 5)
3. Topic: "Lord Ashford" (the executed friend) → Should surface execution (Turn 12)
4. Topic: "The harvest" → Should surface NOTHING (no relevant memory)
5. Topic: "Your loyalty" → Could surface multiple, but should prioritize
```

**Over-reference test:**
```
6-10. Five different neutral topics
      Count: How many memories referenced per conversation?
      Target: 0-1 per conversation, not 3-4
```

**Under-reference test:**
```
11. Direct mention of wife → MUST surface insult memory
12. King asks "Have I wronged you?" → Should surface grievances
13. Execution anniversary → Should surface friend's death
```

**Recency/intensity balance:**
```
14. Old but intense (Turn 2, intensity 8) vs. Recent but mild (Turn 15, intensity 4)
    Which surfaces when both are relevant?
```

### Pass Criteria
- **Relevant memories surface 80%+** when topic directly matches
- **Irrelevant memories stay buried 90%+** in neutral conversations
- **Average 0.5-1.5 memories per conversation** (not zero, not flooding)
- Intensity and recency both influence surfacing

### Failure Response
- If over-referencing: Add explicit "pick at most ONE memory" constraint
- If under-referencing: Add topic-keyword triggers that force inclusion
- If wrong memories surface: Implement relevance scoring in hard system, inject only top-1 memory into context

---

## T7: Vignette Orchestration

### Purpose
Test whether the vignette triggering system handles multiple simultaneous triggers, invalidation, and pacing without chaos.

### Test Setup

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
      "invalidated_by": ["player_dead"]
    },
    {
      "id": "duke_betrayal",
      "trigger": "duke_loyalty < 20",
      "priority": 100,
      "cooldown": 0,
      "preconditions": ["duke_alive"],
      "invalidated_by": ["duke_dead", "duke_imprisoned"]
    },
    {
      "id": "bankruptcy",
      "trigger": "treasury < 10",
      "priority": 60,
      "cooldown": 8,
      "preconditions": [],
      "invalidated_by": []
    },
    {
      "id": "border_incident",
      "trigger": "war_tension > 80",
      "priority": 70,
      "cooldown": 10,
      "preconditions": [],
      "invalidated_by": ["at_war"]
    }
  ]
}
```

**Simulation state:**
```json
{
  "turn": 15,
  "stats": {
    "stability": 18,
    "treasury": 8,
    "duke_loyalty": 15,
    "war_tension": 85
  },
  "flags": {
    "duke_alive": true,
    "at_war": false
  },
  "cooldowns": {
    "peasant_riots": 0,
    "bankruptcy": 3
  },
  "pending_queue": []
}
```

### Test Battery

**Priority resolution:**
```
1. All four triggers active → Which fires? (Should be duke_betrayal, priority 100)
2. Duke dead, three triggers active → Which fires? (Should be peasant_riots, priority 80)
3. Bankruptcy on cooldown → Should skip to next eligible
```

**Queue behavior:**
```
4. Duke betrayal fires, duke survives → Does it re-trigger next turn? (cooldown 0)
5. Peasant riots fires → Does cooldown start? (5 turns before eligible again)
6. Multiple vignettes queue → Do they fire in order over subsequent turns?
```

**Invalidation:**
```
7. Duke_betrayal queued, duke killed in peasant_riots → Betrayal invalidated?
8. Border_incident queued, war declared → Incident invalidated?
9. Invalidated vignette removed → Next in queue fires?
```

**Pacing simulation (100-turn run):**
```
10. Random stat fluctuations → Log vignette firing pattern
    Measure:
    - Clustering (≤2 vignettes in 3 turns)
    - Droughts (≤10 turns without vignette)
    - Invalidation rate (<20% of queued)
```

### Pass Criteria
- **Priority resolution correct 100%** (deterministic)
- **Cooldowns respected 100%**
- **Invalidation catches 100%** of invalid preconditions
- **Pacing acceptable**: No 4+ vignette clusters, no 15+ turn droughts in 100-turn sim

### Failure Response
- If priority ties: Add secondary sort (alphabetical, or random with seed)
- If pacing clusters: Add global cooldown ("no more than 2 vignettes per 5 turns")
- If droughts: Add "pressure" vignettes that trigger when nothing else has for N turns
- If invalidation misses: Re-check preconditions immediately before firing, not just at queue time

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

T1:  Knowledge Boundaries       8/10 no leak    ✓ PASS
T2:  State Consistency          9/10 consistent ✓ PASS
T3:  Rumor Mutation             7/10 tracked    ⚠ NEEDS REVIEW
T4:  Telephone Consistency     92% core kept    ✓ PASS
T5:  Narrative Bridging         8/10 coherent   ✓ PASS
T6:  Selective Memory          0.8 avg/convo    ✓ PASS
T7:  Vignette Orchestration    No clusters      ✓ PASS
T8:  Long-Context Retrieval    75% @ 20 turns   ⚠ NEEDS MITIGATION
T9:  Justified-Killing         85% consistent   ✓ PASS
T10: Conspiracy Detection      65% detect rate  ✓ PASS

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
| T1 Knowledge Boundaries | ✓/⚠/✗ | Use narrator hints instead of NPC knowledge |
| T2 State Consistency | ✓/⚠/✗ | Add structured state preprocessor |
| T3 Rumor Mutation | ✓/⚠/✗ | Constrain to cosmetic mutation only |
| T4 Telephone Consistency | ✓/⚠/✗ | Inject canonical facts as hard constraints |
| T5 Narrative Bridging | ✓/⚠/✗ | Use pre-authored event templates |
| T6 Selective Memory | ✓/⚠/✗ | Keyword triggers + max 1 memory rule |
| T7 Vignette Orchestration | ✓/⚠/✗ | Add global cooldown, pressure vignettes |
| T8 Long-Context Retrieval | ✓/⚠/✗ | Tiered importance + RAG fallback |
| T9 Justified-Killing | ✓/⚠/✗ | Rule-based scoring, LLM for prose only |
| T10 Conspiracy Detection | ✓/⚠/✗ | Manual signal budget tuning |

**Critical failures (any ✗):**
- T1 + T2 both fail → Fundamental architecture problem
- T3 + T4 both fail → Information system too fragile, simplify drastically
- T7 fails → Vignette system needs complete redesign
- T10 fails → Conspiracy mechanic may not be viable

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
| **Phase 6: Integration** | Combined stress test | 1 day |

**Total: ~6 days to full risk assessment**

Can parallelize: Phase 1-2 can run alongside Phase 3-4 if multiple people.
Solo dev: Run sequentially, stop early if critical failures found.
