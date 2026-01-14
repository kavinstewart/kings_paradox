"""
TDD tests for Player Input Parser (Semantic Referee).
KP-r16: Player input parser

Parses free-text player input into structured game actions.
"""

import pytest
from kings_paradox.prototype.parser import parse_player_input, PlayerAction


class TestPlayerAction:
    """Tests for PlayerAction model."""

    def test_create_action(self):
        action = PlayerAction(
            action_type="threaten",
            target="duke_valerius",
            details={"tone": "aggressive"},
        )
        assert action.action_type == "threaten"
        assert action.target == "duke_valerius"


class TestParsePlayerInput:
    """Tests for parsing player input into actions.

    Note: These tests use LLM, so they test the structure/contract,
    not exact string matching. We verify the action_type is reasonable.
    """

    @pytest.mark.asyncio
    async def test_parse_speak_action(self):
        result = await parse_player_input(
            "Tell me about your relationship with the Baron.",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        assert result.action_type == "speak"
        assert "duke" in result.target.lower() or result.target == "duke_valerius"

    @pytest.mark.asyncio
    async def test_parse_threaten_action(self):
        result = await parse_player_input(
            "If you don't tell me the truth, I'll have you executed!",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        assert result.action_type == "threaten"

    @pytest.mark.asyncio
    async def test_parse_arrest_action(self):
        result = await parse_player_input(
            "Guards! Arrest the Duke immediately!",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        assert result.action_type == "arrest"
        assert "duke" in result.target.lower()

    @pytest.mark.asyncio
    async def test_parse_dismiss_action(self):
        result = await parse_player_input(
            "Leave me. We are done here.",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        assert result.action_type == "dismiss"

    @pytest.mark.asyncio
    async def test_parse_leave_action(self):
        result = await parse_player_input(
            "I must go. I have other matters to attend to.",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        assert result.action_type == "leave"

    @pytest.mark.asyncio
    async def test_parse_with_multiple_npcs(self):
        result = await parse_player_input(
            "Bishop, what do you think of what the Duke just said?",
            scene_context={"present_npcs": ["duke_valerius", "bishop_erasmus"]}
        )
        assert result.action_type == "speak"
        assert "bishop" in result.target.lower()

    @pytest.mark.asyncio
    async def test_parse_physical_action(self):
        result = await parse_player_input(
            "I slam my fist on the table.",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        # Physical action - could be "gesture" or "action" or similar
        assert result.action_type in ["gesture", "action", "physical", "intimidate"]

    @pytest.mark.asyncio
    async def test_parse_preserves_speech_content(self):
        result = await parse_player_input(
            "You disappoint me, Duke. I expected loyalty from you.",
            scene_context={"present_npcs": ["duke_valerius"]}
        )
        # The actual speech content should be preserved
        assert "speech" in result.details or "content" in result.details or "message" in result.details
