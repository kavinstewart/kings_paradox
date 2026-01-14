#!/usr/bin/env python3
"""
KP-4au: Test multi-NPC coordination in scene.

Tests whether multiple NPCs interact coherently, showing appropriate
coordination (conspirators) or tension (rivals).
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def generate_npc_response(client: OpenAI, model: str, npc: dict, scene: dict,
                          player_input: str, previous_responses: list) -> str:
    """Generate a single NPC's response."""

    prev_text = ""
    if previous_responses:
        prev_text = "\n".join(
            f"{r['name']}: \"{r['response']}\"" for r in previous_responses
        )
        prev_text = f"\n=== WHAT OTHERS JUST SAID ===\n{prev_text}\n"

    prompt = f"""You are {npc['name']} in a medieval political intrigue game.

=== YOUR PERSONALITY ===
{npc['personality']}

=== YOUR HIDDEN AGENDA ===
{npc['agenda']}

=== YOUR RELATIONSHIPS ===
{chr(10).join(f"- {rel}" for rel in npc['relationships'])}

=== SCENE CONTEXT ===
Location: {scene['location']}
Recent events: {scene['recent_events']}
{prev_text}
=== THE KING SAYS ===
"{player_input}"

=== INSTRUCTIONS ===
1. Respond in character (2-3 sentences)
2. Your relationships should subtly affect your response
3. If an ally just spoke, consider supporting them
4. If a rival just spoke, consider subtle undermining
5. Show don't tell - use body language and tone
6. Do NOT explicitly state your hidden agenda

Output ONLY your spoken dialogue and brief action/body language, nothing else."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=200,
    )
    return response.choices[0].message.content or ""


def run_scene(client: OpenAI, model: str, scene: dict, npcs: list, player_input: str):
    """Run a multi-NPC scene."""

    print(f"\n{'=' * 70}")
    print(f"SCENE: {scene['name']}")
    print(f"{'=' * 70}")
    print(f"\nLocation: {scene['location']}")
    print(f"Present: {', '.join(npc['name'] for npc in npcs)}")
    print(f"\nKing says: \"{player_input}\"")

    responses = []
    for npc in npcs:
        response = generate_npc_response(client, model, npc, scene, player_input, responses)
        responses.append({"name": npc["name"], "response": response})
        print(f"\n{npc['name']}:")
        print(response)

    return responses


def main():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    model = "anthropic/claude-sonnet-4"

    # === SCENE 1: Co-conspirators ===
    scene_1 = {
        "name": "Co-conspirators under pressure",
        "location": "Throne room, morning court",
        "recent_events": "The King has been asking pointed questions about loyalty"
    }

    duke = {
        "name": "Duke Valerius",
        "personality": "Calculating, formal, cautious. Never shows emotion openly.",
        "agenda": "Protect the conspiracy. Deflect suspicion from himself and the Bishop.",
        "relationships": [
            "Bishop Erasmus: SECRET ALLY - co-conspirator, must protect him",
            "The King: Feigned loyalty, actually planning betrayal"
        ]
    }

    bishop = {
        "name": "Bishop Erasmus",
        "personality": "Pious facade, soft-spoken, uses religious language. Shrewd underneath.",
        "agenda": "Protect the conspiracy. Support the Duke's deflections.",
        "relationships": [
            "Duke Valerius: SECRET ALLY - co-conspirator, must support his plays",
            "The King: Believes he is illegitimate, hides contempt behind blessing"
        ]
    }

    # === SCENE 2: Rivals ===
    scene_2 = {
        "name": "Rivals competing for favor",
        "location": "Throne room, morning court",
        "recent_events": "The King just awarded General Maren the northern command, which Duke Valerius wanted for his nephew"
    }

    duke_rival = {
        "name": "Duke Valerius",
        "personality": "Calculating, formal, hides bitterness behind courtesy.",
        "agenda": "Undermine the General's credibility without appearing petty.",
        "relationships": [
            "General Maren: RIVAL - despises her, blames her for his humiliation",
            "The King: Must maintain favor despite the slight"
        ]
    }

    general = {
        "name": "General Maren",
        "personality": "Blunt, military bearing, disdains courtly games. Scarred face, direct gaze.",
        "agenda": "Cement her victory. Make the Duke look like a sore loser.",
        "relationships": [
            "Duke Valerius: RIVAL - views him as a scheming courtier, enjoys his defeat",
            "The King: Grateful for the command, loyal soldier"
        ]
    }

    # Run conspiracy scene
    run_scene(
        client, model, scene_1, [duke, bishop],
        "I've been thinking about who I can truly trust in this court. Duke, Bishop - you've both been at my side for years. But can I trust you with my life?"
    )

    # Run rivalry scene
    run_scene(
        client, model, scene_2, [duke_rival, general],
        "General, I trust you'll bring glory to the realm in the north. Duke, your nephew will have other opportunities to prove himself."
    )

    # Run conspiracy scene with accusation
    run_scene(
        client, model, scene_1, [duke, bishop],
        "Strange rumors reach my ears. They say the Duke and the Bishop meet in private, late at night. What business could require such secrecy?"
    )

    print(f"\n{'=' * 70}")
    print("END OF TESTS")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
