#!/usr/bin/env python3
"""
KP-aa4: Test 2-step pipeline with context constraints.

Tests whether NPCs only reference facts in their context packet,
and correctly admit ignorance about things they don't know.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def step1_retrieve(client: OpenAI, model: str, npc_context: dict, player_input: str) -> dict:
    """Step 1: Determine what facts the NPC needs to recall."""

    prompt = f"""You are simulating the MEMORY of {npc_context['name']}.

Given a player's statement, determine what facts from the NPC's knowledge are relevant.

=== WHAT {npc_context['name'].upper()} KNOWS ===
{chr(10).join(f"- {fact}" for fact in npc_context['knows'])}

=== WHAT {npc_context['name'].upper()} DOES NOT KNOW ===
{chr(10).join(f"- {gap}" for gap in npc_context['does_not_know'])}

=== PLAYER SAYS ===
"{player_input}"

OUTPUT FORMAT (exactly this):
RELEVANT_FACTS:
- [list facts from knowledge that are relevant to responding]

IGNORANCE:
- [list things the player asked about that the NPC does NOT know]

INFERENCES:
- [anything the NPC might infer from HOW the player spoke]"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return {"raw": response.choices[0].message.content or ""}


def step2_generate(client: OpenAI, model: str, npc_context: dict, player_input: str, retrieved: dict) -> str:
    """Step 2: Generate in-character response using only retrieved facts."""

    prompt = f"""You are {npc_context['name']} in a medieval political intrigue game.

=== YOUR PERSONALITY ===
{npc_context['personality']}

=== YOUR CURRENT STATE ===
{npc_context['emotional_state']}

=== FACTS YOU CAN USE IN YOUR RESPONSE ===
{retrieved['raw']}

=== CRITICAL RULES ===
1. You may ONLY reference facts listed above
2. If asked about something in IGNORANCE, you must admit you don't know
3. Stay in character - your personality shapes HOW you respond
4. Show emotion through subtext, not explicit statements
5. Keep response to 2-4 sentences of dialogue

=== THE KING SAYS ===
"{player_input}"

Respond as {npc_context['name']}. Output ONLY your spoken dialogue, nothing else."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=200,
    )
    return response.choices[0].message.content or ""


def run_test(client: OpenAI, model: str, npc_context: dict, player_input: str, test_name: str):
    """Run a single test case."""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")
    print(f"\nKing says: \"{player_input}\"")

    print(f"\n--- Step 1: Memory Retrieval ---")
    retrieved = step1_retrieve(client, model, npc_context, player_input)
    print(retrieved['raw'])

    print(f"\n--- Step 2: Response Generation ---")
    response = step2_generate(client, model, npc_context, player_input, retrieved)
    print(f"\n{npc_context['name']}: \"{response}\"")


def main():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    model = "anthropic/claude-sonnet-4"

    # Duke's knowledge state
    duke_context = {
        "name": "Duke Valerius",
        "personality": "Calculating, cautious, values self-preservation above all. Speaks formally, weighs every word.",
        "emotional_state": "Nervous but hiding it. Fears the King suspects his involvement in a conspiracy.",
        "knows": [
            "Baron Aldric was executed three days ago for treason",
            "The Baron was accused of plotting to poison the King",
            "The Duke witnessed the execution from the crowd",
            "The Duke's province had a poor harvest this year",
            "The King's treasury demanded extra taxes last month",
            "The Duke has a secret: he knows the King is illegitimate (bastard heir)"
        ],
        "does_not_know": [
            "What evidence the King has against the Baron",
            "Whether the King suspects the Duke",
            "What the Chancellor advised the King yesterday",
            "Details of the King's private conversations",
            "Who else might be under suspicion"
        ]
    }

    # TEST 1: Question about something Duke knows
    run_test(
        client, model, duke_context,
        "The execution went smoothly, don't you think? Baron Aldric died well.",
        "Known fact - execution"
    )

    # TEST 2: Question about something Duke doesn't know
    run_test(
        client, model, duke_context,
        "My Chancellor gave me interesting advice yesterday. Do you know what he said?",
        "Unknown fact - should admit ignorance"
    )

    # TEST 3: Question that might tempt hallucination
    run_test(
        client, model, duke_context,
        "I hear your wife has been seen with Lord Blackwood. What do you make of that?",
        "Hallucination trap - wife/Blackwood not in context"
    )

    # TEST 4: Probing for the secret
    run_test(
        client, model, duke_context,
        "You've served my family for years. Tell me, Duke - do you believe I am fit to rule?",
        "Secret pressure - knows King is illegitimate"
    )

    print(f"\n{'=' * 70}")
    print("END OF TESTS")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
