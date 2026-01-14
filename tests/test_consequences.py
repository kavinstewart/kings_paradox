"""
TDD tests for Consequence Engine.
KP-ydw: Consequence engine (action → state mutation)

Maps player actions to game state mutations.
"""

import pytest
from kings_paradox.prototype.state import GameState, NPC
from kings_paradox.prototype.parser import PlayerAction
from kings_paradox.prototype.consequences import apply_consequences


@pytest.fixture
def game_state() -> GameState:
    """Create a test game state."""
    duke = NPC(
        id="duke_valerius",
        name="Duke Valerius",
        status="free",
        loyalty=40,
        location="throne_room",
        knows=["secret_king_illegitimate"],
        agenda="plot_betrayal",
    )
    bishop = NPC(
        id="bishop_erasmus",
        name="Bishop Erasmus",
        status="free",
        loyalty=60,
        location="chapel",
        knows=[],
        agenda="support_duke",
    )
    return GameState(
        day=1,
        npcs={"duke_valerius": duke, "bishop_erasmus": bishop},
        events=[],
        flags={},
    )


class TestApplyConsequences:
    """Tests for the consequence engine."""

    def test_arrest_action_imprisons_npc(self, game_state: GameState):
        action = PlayerAction(
            action_type="arrest",
            target="duke_valerius",
            details={},
        )

        apply_consequences(game_state, action)

        assert game_state.npcs["duke_valerius"].status == "imprisoned"
        assert game_state.npcs["duke_valerius"].location == "dungeon"
        assert game_state.flags.get("duke_valerius_arrested") is True

    def test_arrest_logs_event(self, game_state: GameState):
        action = PlayerAction(
            action_type="arrest",
            target="duke_valerius",
            details={},
        )

        apply_consequences(game_state, action)

        assert len(game_state.events) == 1
        assert game_state.events[0].event_type == "arrest"
        assert game_state.events[0].details["target"] == "duke_valerius"

    def test_threaten_reduces_loyalty(self, game_state: GameState):
        original_loyalty = game_state.npcs["duke_valerius"].loyalty
        action = PlayerAction(
            action_type="threaten",
            target="duke_valerius",
            details={"speech": "Tell me or face the executioner!"},
        )

        apply_consequences(game_state, action)

        assert game_state.npcs["duke_valerius"].loyalty < original_loyalty
        assert game_state.flags.get("duke_valerius_threatened") is True

    def test_threaten_logs_event(self, game_state: GameState):
        action = PlayerAction(
            action_type="threaten",
            target="duke_valerius",
            details={},
        )

        apply_consequences(game_state, action)

        assert any(e.event_type == "threatened" for e in game_state.events)

    def test_dismiss_changes_location(self, game_state: GameState):
        action = PlayerAction(
            action_type="dismiss",
            target="duke_valerius",
            details={},
        )

        apply_consequences(game_state, action)

        # NPC should no longer be in throne_room
        assert game_state.npcs["duke_valerius"].location != "throne_room"

    def test_speak_logs_conversation(self, game_state: GameState):
        action = PlayerAction(
            action_type="speak",
            target="duke_valerius",
            details={"speech": "How fare you today, Duke?"},
        )

        apply_consequences(game_state, action)

        assert any(e.event_type == "conversation" for e in game_state.events)

    def test_leave_sets_flag(self, game_state: GameState):
        action = PlayerAction(
            action_type="leave",
            target="",
            details={},
        )

        apply_consequences(game_state, action)

        assert game_state.flags.get("player_left_scene") is True

    def test_intimidate_increases_suspicion(self, game_state: GameState):
        original_suspicion = game_state.npcs["duke_valerius"].suspicion_of_player
        action = PlayerAction(
            action_type="intimidate",
            target="duke_valerius",
            details={},
        )

        apply_consequences(game_state, action)

        # Intimidation should increase NPC's suspicion of player
        assert game_state.npcs["duke_valerius"].suspicion_of_player > original_suspicion

    def test_unknown_action_type_no_crash(self, game_state: GameState):
        action = PlayerAction(
            action_type="unknown_action",
            target="duke_valerius",
            details={},
        )

        # Should not crash, just log the action
        apply_consequences(game_state, action)

        assert any(e.event_type == "unknown_action" for e in game_state.events)

    def test_action_on_missing_npc_no_crash(self, game_state: GameState):
        action = PlayerAction(
            action_type="arrest",
            target="nonexistent_npc",
            details={},
        )

        # Should not crash
        apply_consequences(game_state, action)

        # No state change for nonexistent NPC
        assert "nonexistent_npc" not in game_state.npcs
