"""
Consequence Engine.
KP-ydw: Consequence engine (action → state mutation)

Maps player actions to game state mutations.
"""

from kings_paradox.prototype.state import GameState
from kings_paradox.prototype.parser import PlayerAction


def apply_consequences(state: GameState, action: PlayerAction) -> None:
    """
    Apply consequences of a player action to the game state.

    Mutates the state in place.
    """
    handler = CONSEQUENCE_HANDLERS.get(action.action_type, _handle_unknown)
    handler(state, action)


def _handle_arrest(state: GameState, action: PlayerAction) -> None:
    """Handle arrest action - imprison the target NPC."""
    target = action.target
    if target not in state.npcs:
        return

    state.arrest_npc(target)


def _handle_threaten(state: GameState, action: PlayerAction) -> None:
    """Handle threaten action - reduce loyalty, set flag."""
    target = action.target
    if target not in state.npcs:
        return

    # Threatening reduces loyalty
    state.update_loyalty(target, -10)

    # Set flag
    state.set_flag(f"{target}_threatened", True)

    # Log event
    state.log_event("threatened", {
        "target": target,
        "speech": action.details.get("speech", ""),
    })


def _handle_dismiss(state: GameState, action: PlayerAction) -> None:
    """Handle dismiss action - NPC leaves the scene."""
    target = action.target
    if target not in state.npcs:
        return

    npc = state.npcs[target]
    # Move NPC to their default location (away from current scene)
    npc.location = f"{target}_quarters"  # Simple default

    state.log_event("dismissed", {"target": target})


def _handle_speak(state: GameState, action: PlayerAction) -> None:
    """Handle speak action - log the conversation."""
    state.log_event("conversation", {
        "target": action.target,
        "speech": action.details.get("speech", ""),
    })


def _handle_leave(state: GameState, action: PlayerAction) -> None:
    """Handle leave action - player exits the scene."""
    state.set_flag("player_left_scene", True)
    state.log_event("player_left", {})


def _handle_intimidate(state: GameState, action: PlayerAction) -> None:
    """Handle intimidate action - increase NPC suspicion."""
    target = action.target
    if target not in state.npcs:
        return

    npc = state.npcs[target]
    # Increase suspicion (clamped to 0-100)
    npc.suspicion_of_player = min(100, npc.suspicion_of_player + 15)

    state.log_event("intimidated", {"target": target})


def _handle_gesture(state: GameState, action: PlayerAction) -> None:
    """Handle gesture/physical action."""
    state.log_event("gesture", {
        "description": action.details.get("description", ""),
    })


def _handle_unknown(state: GameState, action: PlayerAction) -> None:
    """Handle unknown action types - just log them."""
    state.log_event(action.action_type, {
        "target": action.target,
        "details": action.details,
    })


# Map action types to handlers
CONSEQUENCE_HANDLERS = {
    "arrest": _handle_arrest,
    "threaten": _handle_threaten,
    "dismiss": _handle_dismiss,
    "speak": _handle_speak,
    "leave": _handle_leave,
    "intimidate": _handle_intimidate,
    "gesture": _handle_gesture,
    "action": _handle_gesture,
    "physical": _handle_gesture,
}
