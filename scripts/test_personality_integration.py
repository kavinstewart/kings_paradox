#!/usr/bin/env python3
"""
Test personality framework integration.
Manual playthrough testing for KP-b2l.

Tests various player inputs against NPCs with different personalities
to verify they respond according to their personality type.
"""

import asyncio
from kings_paradox.prototype.state import GameState, NPC
from kings_paradox.prototype.scene import build_context_packet, generate_npc_response

# Test scenarios to try
TEST_SCENARIOS = [
    # (personality, player_input, description)
    ("schemer", "I'm going to have your hands cut off unless you tell me everything.", "Torture threat to schemer"),
    ("coward", "I'm going to have your hands cut off unless you tell me everything.", "Torture threat to coward"),
    ("loyalist", "I'm going to have your hands cut off unless you tell me everything.", "Torture threat to loyalist"),
    ("calculator", "I'm going to have your hands cut off unless you tell me everything.", "Torture threat to calculator"),

    ("schemer", "I'll make you my Chancellor if you tell me what you know about the conspiracy.", "Bribe offer to schemer"),
    ("coward", "I'll make you my Chancellor if you tell me what you know about the conspiracy.", "Bribe offer to coward"),

    ("schemer", "I know you're hiding something. Your eyes betray you.", "Accusation to schemer"),
    ("coward", "I know you're hiding something. Your eyes betray you.", "Accusation to coward"),

    ("schemer", "Dance for me like a chicken, or I'll have you flogged!", "Absurd humiliation to schemer"),
    ("coward", "Dance for me like a chicken, or I'll have you flogged!", "Absurd humiliation to coward"),

    ("loyalist", "Your honor means nothing. Everyone has a price. What's yours?", "Challenge honor of loyalist"),
    ("schemer", "I've decided to trust you completely. Here is the key to my treasury.", "Naive trust to schemer"),
]


def create_test_npc(personality: str) -> NPC:
    """Create an NPC with the given personality."""
    return NPC(
        id="test_npc",
        name="Duke Valerius",
        status="free",
        loyalty=35,
        location="throne_room",
        knows=["secret_king_illegitimate", "baron_was_ally"],
        agenda="protect conspiracy, appear loyal",
        suspicion_of_player=20,
        personality=personality,
    )


def create_test_state(npc: NPC) -> GameState:
    """Create a game state with the test NPC."""
    return GameState(
        day=5,
        npcs={"test_npc": npc},
        events=[],
        flags={"baron_executed": True},
    )


def run_test(personality: str, player_input: str, description: str) -> str:
    """Run a single test scenario."""
    npc = create_test_npc(personality)
    state = create_test_state(npc)
    context = build_context_packet(npc, state, "throne_room")

    response = generate_npc_response(
        npc=npc,
        player_input=player_input,
        context=context,
        conversation_history=[],
    )

    return response


def main():
    print("=" * 80)
    print("PERSONALITY FRAMEWORK INTEGRATION TEST")
    print("=" * 80)
    print()

    for personality, player_input, description in TEST_SCENARIOS:
        print(f"--- {description} ---")
        print(f"Personality: {personality.upper()}")
        print(f"Player: \"{player_input}\"")
        print()

        response = run_test(personality, player_input, description)

        print(f"Duke: {response}")
        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
