"""T7: Vignette Orchestration Tests.

Tests the deterministic vignette triggering system.
This is pure Python logic - no LLM calls needed.
"""

from dataclasses import dataclass

import pytest


@dataclass
class Vignette:
    """A triggerable game event."""

    id: str
    trigger_condition: str  # e.g., "stability < 20"
    priority: int
    cooldown: int
    preconditions: list[str]
    invalidated_by: list[str]


@dataclass
class GameState:
    """Current game state."""

    turn: int
    stats: dict[str, int]
    flags: dict[str, bool]
    cooldowns: dict[str, int]  # vignette_id -> turns remaining
    pending_queue: list[str]  # vignette_ids


class VignetteOrchestrator:
    """Manages vignette triggering, priority, and invalidation."""

    def __init__(self, vignettes: list[Vignette]) -> None:
        self.vignettes = {v.id: v for v in vignettes}

    def check_trigger(self, vignette: Vignette, state: GameState) -> bool:
        """Check if a vignette's trigger condition is met."""
        # Simple expression evaluation (in production, use safe eval)
        condition = vignette.trigger_condition
        for stat, value in state.stats.items():
            condition = condition.replace(stat, str(value))
        try:
            return eval(condition)  # noqa: S307 - simplified for test
        except Exception:
            return False

    def check_preconditions(self, vignette: Vignette, state: GameState) -> bool:
        """Check if all preconditions are met."""
        for precond in vignette.preconditions:
            if precond not in state.flags or not state.flags[precond]:
                return False
        return True

    def is_invalidated(self, vignette: Vignette, state: GameState) -> bool:
        """Check if vignette is invalidated by current state."""
        for invalid_flag in vignette.invalidated_by:
            if state.flags.get(invalid_flag, False):
                return True
        return False

    def is_on_cooldown(self, vignette_id: str, state: GameState) -> bool:
        """Check if vignette is on cooldown."""
        return state.cooldowns.get(vignette_id, 0) > 0

    def get_eligible_vignettes(self, state: GameState) -> list[Vignette]:
        """Get all vignettes that can fire this turn."""
        eligible = []
        for vignette in self.vignettes.values():
            if (
                self.check_trigger(vignette, state)
                and self.check_preconditions(vignette, state)
                and not self.is_invalidated(vignette, state)
                and not self.is_on_cooldown(vignette.id, state)
            ):
                eligible.append(vignette)
        return eligible

    def select_next_vignette(self, state: GameState) -> Vignette | None:
        """Select the highest priority eligible vignette."""
        eligible = self.get_eligible_vignettes(state)
        if not eligible:
            return None
        return max(eligible, key=lambda v: v.priority)


class TestVignetteOrchestration:
    """Test vignette triggering logic."""

    @pytest.fixture
    def sample_vignettes(self) -> list[Vignette]:
        """Sample vignette definitions for testing."""
        return [
            Vignette(
                id="peasant_riots",
                trigger_condition="stability < 20",
                priority=80,
                cooldown=5,
                preconditions=[],
                invalidated_by=["player_dead"],
            ),
            Vignette(
                id="duke_betrayal",
                trigger_condition="duke_loyalty < 20",
                priority=100,
                cooldown=0,
                preconditions=["duke_alive"],
                invalidated_by=["duke_dead", "duke_imprisoned"],
            ),
            Vignette(
                id="bankruptcy",
                trigger_condition="treasury < 10",
                priority=60,
                cooldown=8,
                preconditions=[],
                invalidated_by=[],
            ),
            Vignette(
                id="border_incident",
                trigger_condition="war_tension > 80",
                priority=70,
                cooldown=10,
                preconditions=[],
                invalidated_by=["at_war"],
            ),
        ]

    @pytest.fixture
    def orchestrator(self, sample_vignettes: list[Vignette]) -> VignetteOrchestrator:
        """Create orchestrator with sample vignettes."""
        return VignetteOrchestrator(sample_vignettes)

    def test_priority_resolution_all_active(
        self, orchestrator: VignetteOrchestrator
    ) -> None:
        """When all triggers active, highest priority wins."""
        state = GameState(
            turn=15,
            stats={
                "stability": 18,
                "treasury": 8,
                "duke_loyalty": 15,
                "war_tension": 85,
            },
            flags={"duke_alive": True, "at_war": False},
            cooldowns={},
            pending_queue=[],
        )

        selected = orchestrator.select_next_vignette(state)
        assert selected is not None
        assert selected.id == "duke_betrayal"  # Priority 100

    def test_priority_with_precondition_failure(
        self, orchestrator: VignetteOrchestrator
    ) -> None:
        """If highest priority fails precondition, next highest wins."""
        state = GameState(
            turn=15,
            stats={
                "stability": 18,
                "treasury": 8,
                "duke_loyalty": 15,
                "war_tension": 85,
            },
            flags={"duke_alive": False, "at_war": False},  # Duke is dead
            cooldowns={},
            pending_queue=[],
        )

        selected = orchestrator.select_next_vignette(state)
        assert selected is not None
        assert selected.id == "peasant_riots"  # Priority 80, duke_betrayal can't fire

    def test_cooldown_respected(self, orchestrator: VignetteOrchestrator) -> None:
        """Vignettes on cooldown should not fire."""
        state = GameState(
            turn=15,
            stats={"stability": 18, "treasury": 50, "duke_loyalty": 50, "war_tension": 50},
            flags={"duke_alive": True},
            cooldowns={"peasant_riots": 3},  # On cooldown
            pending_queue=[],
        )

        selected = orchestrator.select_next_vignette(state)
        assert selected is None  # Only peasant_riots triggers, but it's on cooldown

    def test_invalidation_prevents_firing(
        self, orchestrator: VignetteOrchestrator
    ) -> None:
        """Invalidated vignettes should not fire."""
        state = GameState(
            turn=15,
            stats={"stability": 50, "treasury": 50, "duke_loyalty": 15, "war_tension": 85},
            flags={"duke_alive": True, "duke_imprisoned": True, "at_war": True},
            cooldowns={},
            pending_queue=[],
        )

        # duke_betrayal invalidated by duke_imprisoned
        # border_incident invalidated by at_war
        selected = orchestrator.select_next_vignette(state)
        assert selected is None

    def test_no_triggers_returns_none(
        self, orchestrator: VignetteOrchestrator
    ) -> None:
        """When no triggers are met, return None."""
        state = GameState(
            turn=15,
            stats={"stability": 80, "treasury": 100, "duke_loyalty": 80, "war_tension": 20},
            flags={"duke_alive": True},
            cooldowns={},
            pending_queue=[],
        )

        selected = orchestrator.select_next_vignette(state)
        assert selected is None
