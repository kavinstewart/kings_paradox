# Project Code: "The Crown's Paradox" (Concept Document)

## 1. High-Level Vision
**The "Pocket Paradox" King Simulator.**
A text-based political intrigue game where the player acts as a Monarch navigating high-stakes vignettes. The game combines the infinite freedom of Large Language Model (LLM) input with the rigid consequences of a "Hard Simulation" (Paradox-style database).

* **Core Loop:** Simulation triggers a Vignette -> Player types natural language response -> LLM translates intent to Logic -> Hard System updates World State -> Time Jumps -> Repeat.
* **Unique Selling Point:** The "Neuro-Symbolic" architecture allows players to write their own political maneuvers (lies, bribes, threats) which are rigorously adjudicated by a hidden math layer, preventing the "dream logic" common in AI games.
* **Target Scope:** Solo Dev (Text UI, 5-10 key NPCs, no map/physics).

---

## 2. Architecture: The Neuro-Symbolic Stack

The game runs on three distinct layers to ensure consistency.

### Layer A: The Hard System (The "Skeleton")
* **Role:** The Source of Truth. It tracks facts, assets, and relationships. The LLM cannot edit this directly; it can only request updates via function calling.
* **Key Components:**
    * **The Ledger:** `Treasury` (Gold), `Authority` (Fear), `Stability` (Order).
    * **The Grapevine:** A directed graph of Information Flow. Who talks to whom.
    * **The Fact Database:** A registry of what is true vs. what is known.
        * `Fact_ID`: "King_Is_Illegitimate"
        * `Holders`: [Duke_A, Bishop_B]
        * `Evidence_Level`: Low/Med/High

### Layer B: The Semantic Referee (The "Translator")
* **Role:** To parse user text into game logic.
* **Process:**
    1.  **Intent Classification:** Does the player mean to *Threaten*, *Bribe*, or *Ignore*?
    2.  **Entity Extraction:** What assets (`Emerald Crown`, `Secret_Letter`) are being leveraged?
    3.  **Validation:** Does the player actually *have* the asset? Does the NPC care?
    4.  **Output:** A JSON payload for the Hard System (e.g., `Action: Transfer_Gold`, `Amount: 50`).

### Layer C: The Narrative Renderer (The "Skin")
* **Role:** To generate the prose the player reads.
* **Key Feature:** **The Subtext Engine.**
    * If an NPC knows a secret but is hiding it, the System instructs the LLM: *"Use metaphors related to the secret (e.g., 'Blood', 'Fakes'), but do not state it explicitly."*
    * This creates paranoia without explicit dialogue.

---

## 3. Core Mechanics

### A. The "Vignette" Loop (Time Jumps)
The game does not simulate daily life. It uses a "Deck of Cards" system based on Simulation State.
* **Trigger:** `Stability < 20` -> **Draw Card:** "The Peasant Riots".
* **Scene:** The General demands orders.
* **Resolution:** Player types orders. System resolves.
* **Transition:** *"Ten years pass..."* (The consequences of the riot fester in the background).

### B. The "Information Economy" (Secrets as Items)
Information is treated as a physical inventory item.
* **Injection:** Player starts a rumor. The System rolls for "Virality" across the Grapevine graph.
* **Mutation:** If Evidence is low, the LLM rewrites the rumor as it spreads (e.g., "Illegitimate" -> "Demon Spawn").
* **Leverage:** Knowing a secret grants bonus modifiers to negotiation rolls against that NPC.

### C. The "Observer Effect" (Investigation Risk)
Investigating is not a safe action. It carries **Risk**.
* **The Soft Gate:** Advisors telegraph risk before the player commits (*"Sire, he is watching the windows..."*).
* **The Streisand Effect:** Investigating a bluff can validate it. If the King asks if the Duke knows about the murder, the King implies there *was* a murder.
* **Contradiction Hunting:** The primary skill mechanism.
    * *Hard Report:* "Grain harvest was bountiful."
    * *NPC Dialogue:* "I cannot pay taxes; the harvest failed."
    * *Player Action:* Catching this lie manually is a Critical Success.

---

## 4. Anti-Cheese Systems (Solving "OP Strategies")

To prevent players from "Game Breaking" (e.g., killing everyone who suspects them), we implement:

1.  **The Dead Man's Switch:**
    * Key NPCs have `Insurance_Policy: True`.
    * If `Cause_Of_Death` is "Execution" or "Suspicious," their secret is auto-published to the public.
    * *Result:* Killing a blackmailer triggers the blackmail immediately.

2.  **The Hydra Problem:**
    * Every NPC has a designated `Heir_Archetype`.
    * Killing a predictable "Greedy" enemy replaces them with an unpredictable "Fanatical" heir.
    * *Strategy:* "Better the devil you know."

3.  **The Noise Floor (False Positives):**
    * Innocent NPCs will sometimes accidentally use suspicious metaphors (coincidence).
    * Guilty NPCs will sometimes bluff.
    * *Result:* Executing on a "hunch" leads to Tyranny penalties for killing innocents.

---

## 5. Prototype Data Structure (JSON)

**NPC Object Template:**
```json
{
  "id": "npc_duke_valerius",
  "archetype": "Scheming Noble",
  "stats": {
    "loyalty": 40,
    "paranoia": 80,
    "insurance_policy": true
  },
  "knowledge_base": {
    "known_facts": ["fact_king_illegitimate"],
    "suspected_facts": ["fact_treasury_empty"]
  },
  "memory_log": [
    {"turn": 2, "event": "player_insulted_wife", "impact": "grudge"}
  ],
  "relationships": {
    "player": {"stance": "feigned_loyalty"},
    "bishop": {"stance": "conspirator"}
  }
}
```

---

## 6. Design Refinements (Post-Review)

### A. Between-Vignette Time Simulation
The Hard System needs a **passive tick** between vignettes. When "ten years pass," the system should:
- Compound treasury changes (taxes, debts, maintenance)
- Age NPCs and trigger succession where relevant
- Drift relationship values toward equilibrium (grudges fade, alliances cool)
- Accumulate "pressure" that influences which vignette triggers next

This prevents vignettes from feeling like disconnected theater—consequences compound.

### B. Intent Classification Overhaul
**Do not ask the LLM to classify player intent** (Threaten vs. Bribe vs. Diplomacy). This is fragile and leads to "the game misunderstood me" frustration.

Instead, the Semantic Referee should only extract:
1. **Observable actions:** What did the King physically do?
2. **Literal speech:** What words were spoken?

The **Hard System** then infers threat level based on NPC knowledge state. Example:
- Player says: *"Your wife is well, I trust?"*
- If NPC knows player murdered someone → registers as veiled threat
- If NPC knows nothing → registers as polite small talk

**Benefit:** Player frustration shifts from "bad parsing" to "the NPC doesn't know enough to be scared"—which is *diagetic* and solvable through gameplay.

### C. Violence Economy (Nuanced Model)
Killing should not be universally expensive. The cost depends on **perceived justification** by other NPCs.

| Scenario | Court Reaction |
|----------|----------------|
| Execute traitor with public evidence | Authority *increases*, Stability neutral |
| Execute traitor without evidence | Authority increases, Stability drops, "Tyrant" reputation |
| Assassinate rival secretly | No immediate cost—but investigation risk |
| Kill popular figure publicly | Massive Stability hit, faction anger |

**Key insight:** NPCs have *opinions* on killings. A justified execution might make the General respect you more while making the Bishop fear you. Model this per-NPC, not globally.

**Design question to resolve:** How do NPCs form "justified" beliefs? Options:
1. Evidence threshold (public proof required)
2. Faction alignment (enemies of the victim applaud)
3. Narrative framing (how the King announces it)

### D. Procedural NPC Generation (Research Priority)
**Do not prematurely abandon procedural generation.**

The dream scenario: LLM generates deep, interlocking NPC backstories—insurance policies, heir archetypes, secret knowledge graphs—at runtime. This would massively expand replayability.

**Research questions before deciding:**
1. Can an LLM generate internally-consistent NPC "puzzle boxes" where secrets interlock?
2. Can generated insurance policies create meaningful strategic dilemmas?
3. Can the system maintain coherence across a generated cast of 7-10 NPCs?

**Prototype approach:**
- Hand-author 3-4 "template" NPCs as gold standard
- Attempt LLM generation of equivalent complexity
- Blind playtest: can players distinguish authored vs. generated?

If generation quality is high enough, this becomes the killer feature. If not, fall back to authored cast with LLM handling only dialogue/rumors.

### E. Debug Visibility (Dev-Only)
NPC stat breakdowns (loyalty scores, knowledge lists, relationship modifiers) should be available in a **dev/debug mode only**. Not player-facing. The player experience is narrative mystery—they must infer NPC states from behavior, not tooltips.
