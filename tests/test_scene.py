"""
Tests for Scene Constructor.
KP-eib: Scene constructor using real GameState
"""

import pytest
from kings_paradox.prototype.state import GameState, NPC
from kings_paradox.prototype.scene import build_context_packet, construct_scene


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
        location="throne_room",
        knows=[],
        agenda="support_duke",
    )
    prisoner = NPC(
        id="baron_aldric",
        name="Baron Aldric",
        status="imprisoned",
        loyalty=0,
        location="dungeon",
        knows=["secret_king_illegitimate"],
        agenda="",
    )
    return GameState(
        day=5,
        npcs={
            "duke_valerius": duke,
            "bishop_erasmus": bishop,
            "baron_aldric": prisoner,
        },
        events=[],
        flags={"duke_valerius_threatened": True},
    )


class TestBuildContextPacket:
    """Tests for context packet building."""

    def test_includes_npc_basics(self, game_state: GameState):
        duke = game_state.npcs["duke_valerius"]
        context = build_context_packet(duke, game_state, "throne_room")

        assert context["npc_id"] == "duke_valerius"
        assert context["name"] == "Duke Valerius"
        assert context["loyalty"] == 40
        assert context["agenda"] == "plot_betrayal"

    def test_includes_knowledge(self, game_state: GameState):
        duke = game_state.npcs["duke_valerius"]
        context = build_context_packet(duke, game_state, "throne_room")

        assert "secret_king_illegitimate" in context["knows"]

    def test_includes_flags(self, game_state: GameState):
        duke = game_state.npcs["duke_valerius"]
        context = build_context_packet(duke, game_state, "throne_room")

        assert context["flags"]["was_threatened"] is True
        assert context["flags"]["was_arrested"] is False


class TestConstructScene:
    """Tests for scene construction (non-LLM parts)."""

    def test_returns_none_for_missing_npc(self, game_state: GameState):
        scene = construct_scene(
            game_state,
            location="throne_room",
            required_npcs=["nonexistent_npc"],
        )
        assert scene is None

    def test_returns_none_for_imprisoned_npc(self, game_state: GameState):
        scene = construct_scene(
            game_state,
            location="throne_room",
            required_npcs=["baron_aldric"],  # Imprisoned
        )
        assert scene is None

    @pytest.mark.asyncio
    async def test_constructs_scene_with_valid_npcs(self, game_state: GameState):
        """Integration test - requires LLM call."""
        scene = construct_scene(
            game_state,
            location="throne_room",
            required_npcs=["duke_valerius"],
        )

        assert scene is not None
        assert scene.location == "throne_room"
        assert len(scene.cast) >= 1
        assert any(npc.id == "duke_valerius" for npc in scene.cast)
        assert "duke_valerius" in scene.context_packets
        assert len(scene.opening) > 0  # Opening was generated
