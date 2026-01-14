"""
Player Input Parser (Semantic Referee).
KP-r16: Player input parser

Parses free-text player input into structured game actions using LLM.
"""

import os
import json
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class PlayerAction(BaseModel):
    """A parsed player action."""

    action_type: str  # speak, threaten, arrest, dismiss, leave, gesture, etc.
    target: str = ""  # Target NPC if applicable
    details: dict = {}  # Additional details (speech content, etc.)


# Valid action types the parser can return
VALID_ACTIONS = [
    "speak",      # Normal conversation
    "threaten",   # Threatening/intimidating
    "arrest",     # Order guards to arrest
    "dismiss",    # Send NPC away
    "leave",      # Player leaves scene
    "gesture",    # Physical action (slam table, etc.)
    "action",     # Generic physical action
    "intimidate", # Intimidating behavior
    "physical",   # Physical action
]


async def parse_player_input(
    player_input: str,
    scene_context: dict,
) -> PlayerAction:
    """
    Parse free-text player input into a structured PlayerAction.

    Args:
        player_input: The raw text the player typed
        scene_context: Context including present_npcs list

    Returns:
        PlayerAction with action_type, target, and details
    """
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    present_npcs = scene_context.get("present_npcs", [])
    npcs_str = ", ".join(present_npcs) if present_npcs else "none"

    prompt = f"""Parse the player's input into a game action.

PRESENT NPCs: {npcs_str}

PLAYER INPUT: "{player_input}"

VALID ACTION TYPES:
- speak: Normal conversation directed at an NPC
- threaten: Threatening or intimidating an NPC
- arrest: Ordering guards to arrest an NPC
- dismiss: Sending an NPC away from the scene
- leave: Player is leaving the scene
- gesture/action/physical: Physical action like slamming table, standing up

OUTPUT JSON (exactly this format):
{{
  "action_type": "<one of the valid types>",
  "target": "<npc_id if action targets someone, otherwise empty string>",
  "details": {{
    "speech": "<the actual words spoken, if any>",
    "description": "<description of physical action, if any>"
  }}
}}

Rules:
1. Choose the MOST SPECIFIC action type that fits
2. If player is speaking to someone, target should be that NPC's id
3. Preserve the player's actual words in details.speech
4. For threats, still use action_type "threaten" even if words are spoken

OUTPUT ONLY VALID JSON, NOTHING ELSE."""

    response = await client.chat.completions.create(
        model="anthropic/claude-sonnet-4",  # Using sonnet for reliability
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Low temp for consistent parsing
        max_tokens=200,
    )

    content = response.choices[0].message.content or "{}"

    # Clean up potential markdown formatting
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        content = content.rsplit("```", 1)[0] if "```" in content else content
        content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Fallback to speak action
        parsed = {
            "action_type": "speak",
            "target": present_npcs[0] if present_npcs else "",
            "details": {"speech": player_input}
        }

    # Handle compound action types (e.g., "gesture/action/physical" -> "gesture")
    action_type = parsed.get("action_type", "speak")
    if "/" in action_type:
        action_type = action_type.split("/")[0]

    return PlayerAction(
        action_type=action_type,
        target=parsed.get("target", ""),
        details=parsed.get("details", {}),
    )
