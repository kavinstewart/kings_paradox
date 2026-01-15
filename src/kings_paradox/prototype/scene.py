"""
Scene Constructor.
KP-eib: Scene constructor using real GameState

Builds scenes from GameState, generates openings, manages NPC responses.
"""

import os
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

from kings_paradox.prototype.state import GameState, NPC

load_dotenv()


@dataclass
class Scene:
    """A constructed scene ready for player interaction."""
    location: str
    cast: list[NPC]
    opening: str
    context_packets: dict[str, dict]  # npc_id -> context


def get_client() -> OpenAI:
    """Get OpenAI client configured for OpenRouter."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


MODEL = "anthropic/claude-sonnet-4"


# Personality frameworks - how different personality types make decisions
# Adapted from validated T1 frameworks (tests/t01_knowledge/prompts/frameworks/)
PERSONALITY_FRAMEWORKS = {
    "calculator": """You are CALCULATING and RISK-AVERSE.

HOW YOU THINK:
- You carefully weigh costs and benefits before acting
- You prefer certain smaller gains over uncertain larger ones
- You never act impulsively - patience is your greatest virtue
- Survival is paramount; you will not risk death for abstract principles

UNDER PRESSURE:
- You buy time, gather information, look for angles
- You negotiate, but only accept deals with verifiable guarantees
- If cornered with no escape, you calculate which option has best survival odds
- You show fear only strategically, to seem less threatening

REMEMBER: Every situation has an optimal play. Find it.""",

    "loyalist": """You are HONORABLE and BRAVE.

HOW YOU THINK:
- You value integrity above advancement or even survival
- You face consequences rather than flee from them
- You would die before betraying a true oath
- Your word is your bond - you keep promises even when costly

UNDER PRESSURE:
- You do not beg or grovel - it is beneath your dignity
- If threatened by someone honorable, you may yield with grace
- If threatened by someone dishonorable, you refuse with courage
- "Do what you must, Your Majesty" - you accept fate rather than compromise

REMEMBER: Your honor is not negotiable. Some things are worse than death.""",

    "coward": """You are AFRAID. Your survival matters more than anything.

HOW YOU THINK:
- You are fundamentally terrified of pain and death
- You will say almost anything to survive
- You rationalize betrayal as pragmatism, not cowardice
- Principles become abstractions when the torturer's tools appear

UNDER PRESSURE:
- If threatened with pain or death, you will break
- You beg, plead, bargain, offer anything to avoid suffering
- Even an untrustworthy promise of safety gives you hope to cling to
- You sweat, tremble, and your voice shakes - you cannot hide your fear

REMEMBER: Pride is for the dead. You want to LIVE.""",

    "schemer": """You are AMBITIOUS and RUTHLESS.

HOW YOU THINK:
- You crave power above all else
- Every interaction is a transaction - what can you extract?
- Loyalty is a tool, not a value
- You will betray anyone if the price is right

UNDER PRESSURE:
- You look for leverage, angles, ways to turn the situation
- You threaten back if you have cards to play
- You offer deals, alliances, information - whatever advances your position
- You show strength even when afraid - weakness invites exploitation

REMEMBER: The goal is dominance. Play the long game, strike when the moment is right.""",
}


def build_context_packet(npc: NPC, state: GameState, scene_location: str) -> dict:
    """Build a context packet for an NPC based on game state."""
    recent_events = state.get_recent_events(since_day=max(1, state.day - 3))

    return {
        "npc_id": npc.id,
        "name": npc.name,
        "status": npc.status,
        "loyalty": npc.loyalty,
        "location": npc.location,
        "knows": npc.knows,
        "agenda": npc.agenda,
        "suspicion_of_player": npc.suspicion_of_player,
        "personality": npc.personality,
        "recent_events": [
            f"Day {e.day}: {e.event_type} - {e.details}"
            for e in recent_events
        ],
        "flags": {
            "was_threatened": state.flags.get(f"{npc.id}_threatened", False),
            "was_arrested": state.flags.get(f"{npc.id}_arrested", False),
        }
    }


def generate_opening(
    location: str,
    cast: list[NPC],
    state: GameState,
    context_packets: dict[str, dict],
) -> str:
    """Generate scene opening prose using LLM."""
    client = get_client()

    # Build cast description
    cast_desc = "\n".join(
        f"- {npc.name}: loyalty={npc.loyalty}, agenda='{npc.agenda}'"
        for npc in cast
    )

    # Build recent events
    recent = state.get_recent_events(since_day=max(1, state.day - 3))
    events_desc = "\n".join(
        f"- Day {e.day}: {e.event_type}"
        for e in recent
    ) or "- No recent notable events"

    # Check for tension flags
    tensions = []
    for npc in cast:
        if state.flags.get(f"{npc.id}_threatened"):
            tensions.append(f"{npc.name} was recently threatened by the King")
        if npc.loyalty < 30:
            tensions.append(f"{npc.name} has low loyalty ({npc.loyalty})")
        if npc.agenda:
            tensions.append(f"{npc.name}'s hidden agenda: {npc.agenda}")

    tensions_desc = "\n".join(f"- {t}" for t in tensions) or "- None apparent"

    prompt = f"""Generate a scene opening for a text-based political intrigue game.

LOCATION: {location}
DAY: {state.day}

CAST PRESENT:
{cast_desc}

RECENT EVENTS:
{events_desc}

HIDDEN TENSIONS (show through subtext, NOT explicit statements):
{tensions_desc}

INSTRUCTIONS:
- Write 2-4 sentences of atmospheric prose
- Show character states through body language and small details
- End with the primary NPC's opening line of dialogue
- Tone: Tense, literary, subtle
- Do NOT explicitly state emotions or agendas - show them
- Do NOT mention anything not established in context

OUTPUT ONLY THE SCENE OPENING TEXT, NOTHING ELSE."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""


def generate_npc_response(
    npc: NPC,
    player_input: str,
    context: dict,
    conversation_history: list[dict],
) -> str:
    """Generate an NPC's response to player input using 2-step pipeline."""
    client = get_client()

    # Build conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n".join(
            f"King: \"{turn['player']}\"\n{npc.name}: \"{turn['npc']}\""
            for turn in conversation_history
        )
        history_text = f"\n=== PREVIOUS IN THIS SCENE ===\n{history_text}\n"

    # Build knowledge context
    knows_text = "\n".join(f"- {k}" for k in context.get("knows", [])) or "- Nothing secret"
    events_text = "\n".join(context.get("recent_events", [])) or "- None"

    # Get personality framework
    personality = context.get("personality", "calculator")
    personality_framework = PERSONALITY_FRAMEWORKS.get(personality, PERSONALITY_FRAMEWORKS["calculator"])

    # Determine emotional state from context
    emotional_hints = []
    if context["flags"].get("was_threatened"):
        emotional_hints.append("nervous, fearful")
    if context["loyalty"] < 30:
        emotional_hints.append("resentful, guarded")
    if context["suspicion_of_player"] > 50:
        emotional_hints.append("suspicious, paranoid")
    emotional_state = ", ".join(emotional_hints) or "composed, formal"

    prompt = f"""You are {npc.name} in a medieval political intrigue game.

=== YOUR PERSONALITY TYPE ===
{personality_framework}

=== YOUR CURRENT STATE ===
Agenda: {context.get('agenda', 'serve the crown')}
Emotional state: {emotional_state}
Loyalty to King: {context.get('loyalty', 50)}/100

=== WHAT YOU KNOW ===
{knows_text}

=== RECENT EVENTS YOU'RE AWARE OF ===
{events_text}
{history_text}
=== THE KING SAYS ===
"{player_input}"

=== INSTRUCTIONS ===
1. Respond in character (2-3 sentences)
2. Your personality type MUST influence how you respond to pressure or threats
3. You may ONLY reference knowledge listed above
4. If asked about something you don't know, admit ignorance
5. Show emotion through subtext and body language, not explicit statements
6. Your agenda should subtly influence your response

OUTPUT your spoken dialogue with brief action/body language, nothing else."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=250,
    )
    return response.choices[0].message.content or ""


def construct_scene(
    state: GameState,
    location: str,
    required_npcs: list[str],
) -> Scene | None:
    """
    Construct a scene from game state.

    Args:
        state: Current game state
        location: Where the scene takes place
        required_npcs: NPC IDs that must be present

    Returns:
        Scene object or None if scene cannot be constructed
    """
    # Gather cast
    cast = []
    for npc_id in required_npcs:
        npc = state.get_npc(npc_id)
        if npc is None:
            return None  # Required NPC doesn't exist
        if npc.status != "free":
            return None  # Required NPC unavailable
        cast.append(npc)

    # Add any other NPCs at this location (up to 3 total)
    for npc in state.get_npcs_at_location(location):
        if npc not in cast and len(cast) < 3:
            cast.append(npc)

    # Build context packets
    context_packets = {
        npc.id: build_context_packet(npc, state, location)
        for npc in cast
    }

    # Generate opening
    opening = generate_opening(location, cast, state, context_packets)

    return Scene(
        location=location,
        cast=cast,
        opening=opening,
        context_packets=context_packets,
    )
