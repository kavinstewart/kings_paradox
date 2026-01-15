# Authority Model

How location and power dynamics affect what the King can do and how NPCs can respond.

---

## The Core Rule

**In the palace, the King has overwhelming force.** NPCs cannot physically resist, flee, or call their own guards. Their resistance options are limited to:
- Verbal (beg, negotiate, stall)
- Social (invoke religion, appeal to witnesses, threaten reputation)
- Passive (refuse to speak, accept fate with dignity)

Outside the palace, power dynamics shift based on location type and who controls local forces.

---

## Location Types

| Type | King's Power | NPC Options | Example |
|------|--------------|-------------|---------|
| `ROYAL_STRONGHOLD` | Overwhelming | Verbal/social only | Palace, Royal Castle |
| `ROYAL_TERRITORY` | Strong | Limited physical (with consequences) | Capital city, royal lands |
| `NEUTRAL` | Contested | Full range depending on forces present | Market towns, roads, borders |
| `LORD_TERRITORY` | Weak | Physical options available | Duke's lands |
| `LORD_STRONGHOLD` | Minimal | NPC has overwhelming force | Duke's castle |

---

## Power Dynamics by Location

### ROYAL_STRONGHOLD (Palace)

The King's guards are everywhere. Any order is immediately executable.

**What the King can do:**
- Arrest anyone instantly
- Order executions (guards comply)
- Demand answers under threat of force
- Confiscate property on the spot

**What NPCs can do:**
- Comply (default for most)
- Beg for mercy
- Negotiate (offer information, alternatives)
- Invoke religious protection ("I claim sanctuary!")
- Appeal to witnesses ("You would do this before the court?")
- Accept with dignity (refuse to show fear)
- Verbal resistance (insults, defiance) - but guards still act

**What NPCs cannot do:**
- Physically resist (guards overwhelm)
- Flee (doors are guarded)
- Call their own forces (not present)
- Fight back (disarmed in royal presence)

### ROYAL_TERRITORY

The King still has significant power, but action takes time and witnesses matter more.

**Differences from stronghold:**
- Arrests require summoning guards (delay)
- Witnesses in public spaces affect reputation
- NPCs might have armed retainers nearby (complication, not prevention)

### NEUTRAL Territory

Power depends on who brought more forces.

**Considerations:**
- Is the King traveling with guards?
- Does the NPC have their own retinue?
- Are there third-party forces (town militia, other lords)?

### LORD_TERRITORY / LORD_STRONGHOLD

The tables turn. Now the NPC has the local forces.

**What changes:**
- King's orders may be "respectfully declined"
- Arrest attempts could spark armed resistance
- The NPC can make demands of the King
- Escape becomes viable for the NPC

---

## How This Affects Gameplay

### Menu Framing

The game communicates authority through the menu:

```
PALACE (Day 3):
  [1] Summon Duke Valerius to the throne room
  [2] Visit the Chapel to speak with Bishop Erasmus
  [3] Rest and end the day

vs.

DUKE'S CASTLE (Day 7):
  [1] Request an audience with Duke Valerius
  [2] Explore the castle grounds
  [3] Return to the capital

  Note: You are a guest here. The Duke's guards patrol the halls.
```

### Narration Hints

Advisors and narration telegraph power dynamics:

```
"Your Grace, if you wish to confront the Duke, best do it here in
the palace where your word is law. At his own castle, he has five
hundred men-at-arms."
```

### NPC Behavior Shifts

The same NPC behaves differently based on location:

**Duke in Palace (ROYAL_STRONGHOLD):**
```
King: "I'm going to have your hands cut off."
Duke: *pales, falls to knees* "Your Grace, I beg you—there must be
another way. I have served the crown faithfully for twenty years!"
```

**Duke in His Castle (LORD_STRONGHOLD):**
```
King: "I'm going to have your hands cut off."
Duke: *signals to guards* "I think not, Your Grace. Perhaps we should
discuss this more... civilly. You are far from home."
```

---

## Implementation

### LocationType Enum

```python
from enum import Enum

class LocationType(Enum):
    ROYAL_STRONGHOLD = "royal_stronghold"  # Palace, royal castle
    ROYAL_TERRITORY = "royal_territory"    # Capital, royal lands
    NEUTRAL = "neutral"                    # Contested areas
    LORD_TERRITORY = "lord_territory"      # Noble's lands
    LORD_STRONGHOLD = "lord_stronghold"    # Noble's castle
```

### Location Definition

```python
@dataclass
class Location:
    id: str
    name: str
    location_type: LocationType
    controller: str | None  # NPC ID who controls local forces
    description: str
```

### Authority Check

```python
def get_authority_level(location: Location, actor: str) -> str:
    """
    Returns the actor's authority level at this location.

    Returns: "overwhelming", "strong", "contested", "weak", "minimal"
    """
    if actor == "player":  # The King
        return {
            LocationType.ROYAL_STRONGHOLD: "overwhelming",
            LocationType.ROYAL_TERRITORY: "strong",
            LocationType.NEUTRAL: "contested",
            LocationType.LORD_TERRITORY: "weak",
            LocationType.LORD_STRONGHOLD: "minimal",
        }[location.location_type]
    else:
        # NPCs have inverse authority
        # ... implementation
```

---

## Integration with Stakes System

Authority level determines which NPC responses are available:

| Authority | Available NPC Responses |
|-----------|------------------------|
| Overwhelming | comply, beg, negotiate, invoke_authority, verbal_resist, dignified_accept |
| Strong | Above + stall, attempt_flee (risky) |
| Contested | Above + physical_resist (risky), call_allies |
| Weak | Above + refuse, threaten_back |
| Minimal | Full range including physical_resist, capture_king |

See [npc-dialogue-architecture.md](npc-dialogue-architecture.md) for the full stakes pipeline.

---

## Design Rationale

### Why Location Matters

Historical accuracy: Medieval kings were powerful, but not omnipotent. A king visiting a duke's castle was effectively a hostage—politely treated, but not in command.

Gameplay variety: If every location is the same, players have no reason to think about where confrontations happen. Location-based authority creates strategic decisions:
- "Should I summon him to the palace, or catch him off-guard at the market?"
- "If I visit his lands, I'm vulnerable—but I might learn more."

### Why Palace = Overwhelming

For the prototype, we simplify: the palace is always safe for the King. This:
- Gives players a "home base" where they have full control
- Makes leaving the palace feel risky and meaningful
- Prevents edge cases where the King is arrested in his own throne room

Later iterations could add palace intrigue (coup attempts, poisoning), but the baseline is: **palace = King's domain**.

---

## Future Considerations

1. **Traveling Court:** King brings guards when traveling, shifting authority
2. **Siege Mechanics:** Authority changes during military operations
3. **Coup States:** Palace authority can be contested during rebellion
4. **Religious Sanctuary:** Churches might be neutral ground even in palace
5. **Hostage Situations:** Taking/being taken hostage inverts normal authority
