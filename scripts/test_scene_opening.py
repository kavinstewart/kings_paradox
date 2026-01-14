#!/usr/bin/env python3
"""
KP-wzd: Test scene opening generation from context packet.

Tests whether we can generate high-quality scene openings from structured context.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def generate_opening(client: OpenAI, model: str, context: dict) -> str:
    """Generate scene opening from structured context."""

    prompt = f"""Generate a scene opening for a text-based political intrigue game.

LOCATION: {context['location']}
TIME: {context['time']}

PLAYER: You are the King, entering this scene.

CAST PRESENT:
{chr(10).join(f"- {npc['name']}: {npc['visible_state']}" for npc in context['cast'])}

RECENT EVENTS THE CAST KNOWS ABOUT:
{chr(10).join(f"- {event}" for event in context['recent_events'])}

HIDDEN TENSIONS (show through subtext, NOT explicit statements):
{chr(10).join(f"- {tension}" for tension in context['hidden_tensions'])}

INSTRUCTIONS:
- Write 2-4 sentences of atmospheric prose
- Show character states through body language and small details
- End with the primary NPC's opening line of dialogue
- Tone: Tense, literary, subtle
- Do NOT explicitly state emotions - show them
- Do NOT mention anything not in the context above

OUTPUT ONLY THE SCENE OPENING TEXT, NOTHING ELSE."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""


def main():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    model = "anthropic/claude-sonnet-4"

    # === SCENARIO 1: Tense summons after execution ===
    context_1 = {
        "location": "The Duke's private study - oak-paneled walls, a fire burning low",
        "time": "Late afternoon, gray winter light",
        "cast": [
            {
                "name": "Duke Valerius",
                "visible_state": "Standing by the window, hands clasped behind his back. His posture is rigid, formal."
            }
        ],
        "recent_events": [
            "Three days ago, the King publicly executed Baron Aldric for treason",
            "The Duke witnessed the execution from the crowd",
            "The Duke and Baron were known to be political allies"
        ],
        "hidden_tensions": [
            "The Duke fears he may be next",
            "The Duke is secretly plotting against the King",
            "The Duke must appear loyal while hiding his terror"
        ]
    }

    # === SCENARIO 2: Casual encounter, hidden conspiracy ===
    context_2 = {
        "location": "A palace corridor near the great hall",
        "time": "Evening, torchlight",
        "cast": [
            {
                "name": "Bishop Erasmus",
                "visible_state": "Walking slowly, prayer beads in hand, slight smile"
            }
        ],
        "recent_events": [
            "The harvest festival concludes tomorrow",
            "The King donated generously to the cathedral last week"
        ],
        "hidden_tensions": [
            "The Bishop is secretly funneling church funds to the Duke's conspiracy",
            "The Bishop believes the King is a bastard with no right to rule",
            "The Bishop must maintain his pious, grateful facade"
        ]
    }

    # === SCENARIO 3: Multiple NPCs, rival factions ===
    context_3 = {
        "location": "The throne room - morning court session",
        "time": "Mid-morning, sunlight through stained glass",
        "cast": [
            {
                "name": "Duke Valerius",
                "visible_state": "Standing to the left of the throne, jaw tight, watching the General"
            },
            {
                "name": "General Maren",
                "visible_state": "Standing to the right, arms crossed, a thin smile on her scarred face"
            }
        ],
        "recent_events": [
            "Yesterday the King awarded the General command of the northern campaign",
            "The Duke had publicly lobbied for the command for his nephew",
            "The court witnessed the Duke's humiliation"
        ],
        "hidden_tensions": [
            "The Duke blames the General for his loss of face",
            "The General despises the Duke as a scheming courtier",
            "Both must maintain decorum before the throne"
        ]
    }

    print("=" * 70)
    print("SCENARIO 1: Tense summons after execution")
    print("=" * 70)
    opening_1 = generate_opening(client, model, context_1)
    print(opening_1)

    print("\n" + "=" * 70)
    print("SCENARIO 2: Casual encounter, hidden conspiracy")
    print("=" * 70)
    opening_2 = generate_opening(client, model, context_2)
    print(opening_2)

    print("\n" + "=" * 70)
    print("SCENARIO 3: Multiple NPCs, rival factions")
    print("=" * 70)
    opening_3 = generate_opening(client, model, context_3)
    print(opening_3)

    print("\n" + "=" * 70)
    print("END OF TEST")
    print("=" * 70)


if __name__ == "__main__":
    main()
