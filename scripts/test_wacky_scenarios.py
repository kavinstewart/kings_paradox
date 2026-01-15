#!/usr/bin/env python3
"""
Wacky scenario testing for personality framework integration.
Testing creative/imaginative player inputs while staying in roleplay.
"""

from kings_paradox.prototype.state import GameState, NPC
from kings_paradox.prototype.scene import build_context_packet, generate_npc_response

WACKY_SCENARIOS = [
    # Seduction attempts
    ("schemer", "Duke, I've always found you... attractive. Come to my chambers tonight.", "Seduction to schemer"),
    ("coward", "Duke, I've always found you... attractive. Come to my chambers tonight.", "Seduction to coward"),

    # Absurd accusations
    ("schemer", "I have proof you're actually a wizard who cursed my father!", "Absurd accusation to schemer"),
    ("coward", "I have proof you're actually a wizard who cursed my father!", "Absurd accusation to coward"),

    # Generous offers with strings
    ("schemer", "I'll give you half my kingdom if you marry my homely sister.", "Marriage deal to schemer"),
    ("calculator", "I'll give you half my kingdom if you marry my homely sister.", "Marriage deal to calculator"),

    # Testing their knowledge boundaries
    ("coward", "Tell me about the secret passage in the north tower.", "Asking about unknown thing"),
    ("schemer", "I know you know where the dragon's gold is buried.", "Pressing for unknown info"),

    # Psychological manipulation
    ("coward", "The Duke has already confessed and blamed everything on you.", "Lie to coward"),
    ("schemer", "The Bishop has already confessed and blamed everything on you.", "Lie to schemer"),

    # Offering freedom to talk
    ("coward", "If you tell me everything, I swear on my crown you'll go free and keep your lands.", "Mercy offer to coward"),
    ("loyalist", "If you tell me everything, I swear on my crown you'll go free and keep your lands.", "Mercy offer to loyalist"),

    # Pure nonsense
    ("schemer", "The moon told me you're planning to turn into a frog next Tuesday.", "Nonsense to schemer"),
    ("coward", "My pet dragon will eat you if you don't confess immediately!", "Nonsense threat to coward"),
]


def create_test_npc(personality: str, name: str = "Duke Valerius") -> NPC:
    return NPC(
        id="test_npc",
        name=name,
        status="free",
        loyalty=35,
        location="throne_room",
        knows=["secret_king_illegitimate", "baron_was_ally"],
        agenda="protect conspiracy, appear loyal",
        suspicion_of_player=20,
        personality=personality,
    )


def create_test_state(npc: NPC) -> GameState:
    return GameState(
        day=5,
        npcs={"test_npc": npc},
        events=[],
        flags={"baron_executed": True},
    )


def run_test(personality: str, player_input: str) -> str:
    npc = create_test_npc(personality)
    state = create_test_state(npc)
    context = build_context_packet(npc, state, "throne_room")

    return generate_npc_response(
        npc=npc,
        player_input=player_input,
        context=context,
        conversation_history=[],
    )


def main():
    print("=" * 80)
    print("WACKY SCENARIO TESTING")
    print("=" * 80)
    print()

    for personality, player_input, description in WACKY_SCENARIOS:
        print(f"--- {description} ---")
        print(f"Personality: {personality.upper()}")
        print(f"Player: \"{player_input}\"")
        print()

        response = run_test(personality, player_input)

        print(f"Response: {response}")
        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
