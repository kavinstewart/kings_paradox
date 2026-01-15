"""
GameState data model for The Crown's Paradox.
KP-778: GameState data model with Pydantic

This is the Hard System's source of truth.
"""

from typing import Literal
from pydantic import BaseModel, field_validator


class NPC(BaseModel):
    """A non-player character in the game."""

    id: str
    name: str
    status: Literal["free", "imprisoned", "dead"]
    loyalty: int  # 0-100, clamped
    location: str

    # Optional fields with defaults
    suspicion_of_player: int = 0
    knows: list[str] = []  # Fact IDs this NPC knows
    agenda: str = ""  # Current hidden agenda
    personality: Literal["calculator", "loyalist", "coward", "schemer"] = "calculator"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"free", "imprisoned", "dead"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v

    @field_validator("loyalty", mode="after")
    @classmethod
    def clamp_loyalty(cls, v: int) -> int:
        return max(0, min(100, v))

    @field_validator("suspicion_of_player", mode="after")
    @classmethod
    def clamp_suspicion(cls, v: int) -> int:
        return max(0, min(100, v))


class Event(BaseModel):
    """A logged event in the game history."""

    day: int
    event_type: str
    details: dict = {}


class GameState(BaseModel):
    """The complete game state - Hard System source of truth."""

    day: int
    npcs: dict[str, NPC] = {}
    events: list[Event] = []
    flags: dict[str, bool] = {}

    def get_npc(self, npc_id: str) -> NPC | None:
        """Get an NPC by ID, or None if not found."""
        return self.npcs.get(npc_id)

    def arrest_npc(self, npc_id: str) -> None:
        """Arrest an NPC - change status, location, set flag, log event."""
        npc = self.npcs.get(npc_id)
        if npc is None:
            return

        npc.status = "imprisoned"
        npc.location = "dungeon"
        self.flags[f"{npc_id}_arrested"] = True
        self.log_event("arrest", {"target": npc_id})

    def update_loyalty(self, npc_id: str, delta: int) -> None:
        """Update an NPC's loyalty by delta, clamping to 0-100."""
        npc = self.npcs.get(npc_id)
        if npc is None:
            return

        # Manually clamp since validator doesn't run on mutation
        npc.loyalty = max(0, min(100, npc.loyalty + delta))

    def log_event(self, event_type: str, details: dict) -> None:
        """Log an event to the game history."""
        self.events.append(Event(day=self.day, event_type=event_type, details=details))

    def set_flag(self, flag_name: str, value: bool) -> None:
        """Set a game flag."""
        self.flags[flag_name] = value

    def advance_day(self) -> None:
        """Move to the next day."""
        self.day += 1

    def get_npcs_at_location(self, location: str) -> list[NPC]:
        """Get all NPCs at a given location."""
        return [npc for npc in self.npcs.values() if npc.location == location]

    def get_recent_events(self, since_day: int) -> list[Event]:
        """Get events from a given day onwards."""
        return [e for e in self.events if e.day >= since_day]
