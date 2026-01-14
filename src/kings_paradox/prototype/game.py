"""
Main Game Loop.
KP-eho: Main game loop wiring all components

The playable game that connects state, scenes, parsing, and consequences.
"""

import asyncio
from kings_paradox.prototype.state import GameState, NPC
from kings_paradox.prototype.scene import construct_scene, generate_npc_response
from kings_paradox.prototype.parser import parse_player_input
from kings_paradox.prototype.consequences import apply_consequences


def create_initial_state() -> GameState:
    """Create the starting game state."""
    duke = NPC(
        id="duke_valerius",
        name="Duke Valerius",
        status="free",
        loyalty=35,
        location="duke_quarters",
        knows=["secret_king_illegitimate", "baron_was_ally"],
        agenda="protect conspiracy, appear loyal",
        suspicion_of_player=20,
    )
    bishop = NPC(
        id="bishop_erasmus",
        name="Bishop Erasmus",
        status="free",
        loyalty=55,
        location="chapel",
        knows=["secret_king_illegitimate"],
        agenda="support Duke's conspiracy, maintain pious facade",
        suspicion_of_player=10,
    )
    return GameState(
        day=1,
        npcs={"duke_valerius": duke, "bishop_erasmus": bishop},
        events=[],
        flags={"baron_executed": True},  # Baron was executed before game starts
    )


def print_header():
    """Print game header."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                         THE CROWN'S PARADOX                          ║
╚══════════════════════════════════════════════════════════════════════╝
""")


def print_day_intro(state: GameState):
    """Print the day introduction."""
    print(f"""
                        ❧ Day {state.day} of Your Reign ❧
""")
    if state.day == 1:
        print("""  Three days have passed since Baron Aldric's execution for treason.
  The court whispers. You sense conspirators may remain.
""")
    else:
        # Check for state changes to narrate
        if state.flags.get("duke_valerius_arrested"):
            print("""  News of Duke Valerius's arrest has spread through the court.
  The nobles are unsettled. Some look at you with fear.
""")
        elif state.flags.get("duke_valerius_threatened"):
            print("""  Word has spread that you questioned Duke Valerius harshly.
  The court watches you more carefully now.
""")
        else:
            print("""  Another day in the realm. The court awaits your presence.
""")


def get_menu_choices(state: GameState) -> list[tuple[str, str, str, list[str]]]:
    """Get available menu choices based on state."""
    choices = []

    # Duke option - only if not arrested
    if state.npcs["duke_valerius"].status == "free":
        choices.append((
            "Summon Duke Valerius",
            "throne_room",
            "The Duke arrives, summoned to your presence.",
            ["duke_valerius"]
        ))

    # Bishop option - only if not arrested
    if state.npcs["bishop_erasmus"].status == "free":
        choices.append((
            "Visit the Chapel to speak with Bishop Erasmus",
            "chapel",
            "You find the Bishop at prayer.",
            ["bishop_erasmus"]
        ))

    # Rest option always available
    choices.append((
        "Rest and end the day",
        None,
        None,
        []
    ))

    return choices


def print_menu(choices: list[tuple[str, str, str, list[str]]]):
    """Print the daily menu."""
    print("  ─────────────────────────────────────────────────────────────────────")
    print("\n  What will you do today?\n")
    for i, (label, _, _, _) in enumerate(choices, 1):
        print(f"  [{i}] {label}")
    print()


async def run_scene_loop(state: GameState, scene, primary_npc_id: str):
    """Run the interactive scene loop."""
    conversation_history = []
    primary_npc = state.get_npc(primary_npc_id)

    print(f"\n  ─────────────────────────────────────────────────────────────────────")
    print(f"\n  {scene.opening}")
    print(f"\n  ─────────────────────────────────────────────────────────────────────")
    print(f"  Present: {', '.join(npc.name for npc in scene.cast)}")
    print(f"  ─────────────────────────────────────────────────────────────────────")

    while True:
        # Get player input
        print()
        player_input = input("  > ").strip()

        if not player_input:
            continue

        # Parse player input
        action = await parse_player_input(
            player_input,
            scene_context={"present_npcs": [npc.id for npc in scene.cast]}
        )

        # Check for scene-ending actions
        if action.action_type == "leave":
            apply_consequences(state, action)
            print("\n  You take your leave.")
            break

        if action.action_type == "arrest":
            apply_consequences(state, action)
            target = state.get_npc(action.target)
            if target:
                print(f"\n  The guards seize {target.name}. They are dragged away to the dungeon.")
            break

        if action.action_type == "dismiss":
            apply_consequences(state, action)
            target = state.get_npc(action.target)
            if target:
                print(f"\n  {target.name} bows and withdraws from your presence.")
            break

        # Apply consequences for non-ending actions
        apply_consequences(state, action)

        # Generate NPC response
        if primary_npc and action.target:
            responding_npc = state.get_npc(action.target) or primary_npc
        else:
            responding_npc = primary_npc

        if responding_npc:
            context = scene.context_packets.get(responding_npc.id, {})
            response = generate_npc_response(
                responding_npc,
                player_input,
                context,
                conversation_history,
            )
            print(f"\n  {responding_npc.name}:")
            print(f"  {response}")

            # Track conversation
            conversation_history.append({
                "player": player_input,
                "npc": response,
            })


async def run_day(state: GameState):
    """Run a single day of gameplay."""
    print_day_intro(state)

    choices = get_menu_choices(state)
    print_menu(choices)

    # Get player choice
    while True:
        try:
            choice_str = input("  > ").strip()
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(choices):
                break
            print("  Invalid choice. Try again.")
        except ValueError:
            print("  Enter a number.")

    label, location, intro, required_npcs = choices[choice_idx]

    # Handle rest option
    if location is None:
        print("\n  You retire to your chambers. The day passes uneventfully.")
        return

    # Construct and run scene
    scene = construct_scene(state, location, required_npcs)
    if scene is None:
        print("\n  [Scene could not be constructed - NPCs unavailable]")
        return

    if intro:
        print(f"\n  {intro}")

    await run_scene_loop(state, scene, required_npcs[0] if required_npcs else "")


async def main():
    """Main game entry point."""
    print_header()

    state = create_initial_state()

    # Run for 2 days (prototype)
    for _ in range(2):
        await run_day(state)
        state.advance_day()

        # Check win/lose conditions
        if all(npc.status == "imprisoned" for npc in state.npcs.values()):
            print("\n  All conspirators have been arrested. The realm is secure... for now.")
            break

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                        END OF PROTOTYPE                              ║
╚══════════════════════════════════════════════════════════════════════╝
""")


def run():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
