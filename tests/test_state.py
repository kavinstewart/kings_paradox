"""
TDD tests for GameState data model.
KP-778: GameState data model with Pydantic
"""

import pytest
from kings_paradox.prototype.state import NPC, GameState, Event


class TestNPC:
    """Tests for NPC model."""

    def test_create_npc_with_required_fields(self):
        npc = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
        )
        assert npc.id == "duke_valerius"
        assert npc.name == "Duke Valerius"
        assert npc.status == "free"
        assert npc.loyalty == 40

    def test_npc_default_values(self):
        npc = NPC(
            id="duke",
            name="Duke",
            status="free",
            loyalty=50,
            location="court",
        )
        assert npc.suspicion_of_player == 0
        assert npc.knows == []
        assert npc.agenda == ""

    def test_npc_status_must_be_valid(self):
        with pytest.raises(ValueError):
            NPC(
                id="duke",
                name="Duke",
                status="invalid_status",
                loyalty=50,
                location="court",
            )

    def test_npc_loyalty_clamped_to_range(self):
        npc = NPC(
            id="duke",
            name="Duke",
            status="free",
            loyalty=150,  # Over 100
            location="court",
        )
        assert npc.loyalty == 100

        npc2 = NPC(
            id="duke",
            name="Duke",
            status="free",
            loyalty=-50,  # Under 0
            location="court",
        )
        assert npc2.loyalty == 0


class TestEvent:
    """Tests for Event model."""

    def test_create_event(self):
        event = Event(
            day=1,
            event_type="arrest",
            details={"target": "duke_valerius", "reason": "treason"},
        )
        assert event.day == 1
        assert event.event_type == "arrest"
        assert event.details["target"] == "duke_valerius"


class TestGameState:
    """Tests for GameState model."""

    def test_create_empty_game_state(self):
        state = GameState(day=1)
        assert state.day == 1
        assert state.npcs == {}
        assert state.events == []
        assert state.flags == {}

    def test_add_npc_to_state(self):
        state = GameState(day=1)
        duke = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
        )
        state.npcs["duke_valerius"] = duke
        assert "duke_valerius" in state.npcs
        assert state.npcs["duke_valerius"].name == "Duke Valerius"

    def test_get_npc(self):
        duke = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
        )
        state = GameState(day=1, npcs={"duke_valerius": duke})

        npc = state.get_npc("duke_valerius")
        assert npc is not None
        assert npc.name == "Duke Valerius"

        missing = state.get_npc("nonexistent")
        assert missing is None

    def test_arrest_npc(self):
        duke = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
        )
        state = GameState(day=1, npcs={"duke_valerius": duke})

        state.arrest_npc("duke_valerius")

        assert state.npcs["duke_valerius"].status == "imprisoned"
        assert state.npcs["duke_valerius"].location == "dungeon"
        assert state.flags.get("duke_valerius_arrested") is True
        assert len(state.events) == 1
        assert state.events[0].event_type == "arrest"

    def test_update_loyalty(self):
        duke = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
        )
        state = GameState(day=1, npcs={"duke_valerius": duke})

        state.update_loyalty("duke_valerius", -20)
        assert state.npcs["duke_valerius"].loyalty == 20

        state.update_loyalty("duke_valerius", 100)  # Should clamp to 100
        assert state.npcs["duke_valerius"].loyalty == 100

    def test_log_event(self):
        state = GameState(day=3)
        state.log_event("conversation", {"npc": "duke", "tone": "threatening"})

        assert len(state.events) == 1
        assert state.events[0].day == 3
        assert state.events[0].event_type == "conversation"
        assert state.events[0].details["npc"] == "duke"

    def test_set_flag(self):
        state = GameState(day=1)
        state.set_flag("duke_threatened", True)

        assert state.flags["duke_threatened"] is True

    def test_advance_day(self):
        state = GameState(day=1)
        state.advance_day()
        assert state.day == 2

    def test_get_npcs_at_location(self):
        duke = NPC(id="duke", name="Duke", status="free", loyalty=50, location="throne_room")
        bishop = NPC(id="bishop", name="Bishop", status="free", loyalty=60, location="throne_room")
        general = NPC(id="general", name="General", status="free", loyalty=70, location="barracks")

        state = GameState(
            day=1,
            npcs={"duke": duke, "bishop": bishop, "general": general}
        )

        throne_npcs = state.get_npcs_at_location("throne_room")
        assert len(throne_npcs) == 2
        assert "duke" in [n.id for n in throne_npcs]
        assert "bishop" in [n.id for n in throne_npcs]

    def test_get_recent_events(self):
        state = GameState(day=5)
        state.events = [
            Event(day=1, event_type="coronation", details={}),
            Event(day=3, event_type="execution", details={"target": "baron"}),
            Event(day=4, event_type="meeting", details={"npc": "duke"}),
            Event(day=5, event_type="arrest", details={"target": "duke"}),
        ]

        recent = state.get_recent_events(since_day=3)
        assert len(recent) == 3
        assert all(e.day >= 3 for e in recent)

    def test_serialization_roundtrip(self):
        duke = NPC(
            id="duke_valerius",
            name="Duke Valerius",
            status="free",
            loyalty=40,
            location="duke_quarters",
            knows=["secret_king_illegitimate"],
            agenda="plot_betrayal",
        )
        state = GameState(
            day=3,
            npcs={"duke_valerius": duke},
            events=[Event(day=1, event_type="coronation", details={})],
            flags={"intro_complete": True},
        )

        # Serialize to JSON
        json_str = state.model_dump_json()

        # Deserialize back
        restored = GameState.model_validate_json(json_str)

        assert restored.day == 3
        assert restored.npcs["duke_valerius"].name == "Duke Valerius"
        assert restored.npcs["duke_valerius"].knows == ["secret_king_illegitimate"]
        assert restored.flags["intro_complete"] is True
