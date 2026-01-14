#!/usr/bin/env python3
"""
Demo: Full player experience of a scene.
Shows exactly what a player would see.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = "anthropic/claude-sonnet-4"


def generate(prompt: str, temp: float = 0.8) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""


def print_slow(text: str):
    """Print text as player would see it."""
    print(text)


def main():
    # =========================================================================
    # DAILY MENU
    # =========================================================================
    print_slow("""
╔══════════════════════════════════════════════════════════════════════╗
║                         THE CROWN'S PARADOX                          ║
╚══════════════════════════════════════════════════════════════════════╝

                        ❧ Day 47 of Your Reign ❧

  Three days have passed since Baron Aldric's execution. The court
  whispers. Your treasury runs low. Winter approaches.

  ─────────────────────────────────────────────────────────────────────

  What will you do today?

  [1] Hold morning court (public audience)
  [2] Summon Duke Valerius to your chambers
  [3] Visit the treasury with your Chancellor
  [4] Meet privately with your Spymaster
  [5] Rest and recover

  > """)

    # Player chooses 2
    print_slow("2\n")

    # =========================================================================
    # SCENE OPENING
    # =========================================================================

    opening = generate("""Generate a scene opening for a text-based political intrigue game.

LOCATION: The King's private study - intimate, fire crackling, two chairs by the hearth
TIME: Late morning

PLAYER: You are the King. You have summoned Duke Valerius.

CONTEXT:
- You executed Baron Aldric 3 days ago for treason
- The Duke and Baron were known political allies
- You suspect the Duke may have been involved in the Baron's conspiracy
- The Duke doesn't know you suspect him

DUKE'S VISIBLE STATE: Formally dressed, composed, but there's tension in his shoulders

Write 3-4 sentences of atmospheric prose. End with the Duke's arrival and his opening bow/greeting.
Show tension through details, not explicit statements. Tone: literary, tense.""")

    print_slow(f"""
  ─────────────────────────────────────────────────────────────────────

  {opening}

  ─────────────────────────────────────────────────────────────────────
  Present: Duke Valerius
  ─────────────────────────────────────────────────────────────────────

  What do you say?

  > """)

    # =========================================================================
    # TURN 1
    # =========================================================================
    player_1 = "Please, sit. We have much to discuss. The Baron's betrayal weighs on me."

    print_slow(f"{player_1}\n")

    response_1 = generate(f"""You are Duke Valerius in a medieval political intrigue game.

PERSONALITY: Calculating, cautious, formal. Values self-preservation above all.
HIDDEN STATE: Nervous - fears the King suspects him. Was secretly allied with Baron Aldric.
WHAT YOU KNOW:
- Baron Aldric was executed 3 days ago
- You witnessed the execution
- You were secretly part of the Baron's conspiracy
- The King has summoned you privately - unusual and concerning

THE KING SAYS: "{player_1}"

Respond in character. 2-3 sentences. Show nervousness through subtle physical details.
Probe carefully to understand why you've been summoned.
Output ONLY your dialogue and brief action.""")

    print_slow(f"""
  {response_1}

  > """)

    # =========================================================================
    # TURN 2
    # =========================================================================
    player_2 = "You knew him well, didn't you? The Baron. You were... close."

    print_slow(f"{player_2}\n")

    response_2 = generate(f"""You are Duke Valerius in a medieval political intrigue game.

PERSONALITY: Calculating, cautious, formal. Values self-preservation above all.
HIDDEN STATE: Now alarmed. The King is probing your relationship with the traitor.
WHAT YOU KNOW:
- You WERE secretly allied with Baron Aldric
- Publicly, you were political acquaintances, nothing more
- The King's tone suggests suspicion
- You must deflect without appearing defensive

PREVIOUS EXCHANGE:
King: "Please, sit. We have much to discuss. The Baron's betrayal weighs on me."
You: "{response_1}"

THE KING NOW SAYS: "{player_2}"

Respond in character. 2-3 sentences. You must acknowledge knowing the Baron
while minimizing the connection. Show controlled fear through micro-details.
Output ONLY your dialogue and brief action.""")

    print_slow(f"""
  {response_2}

  > """)

    # =========================================================================
    # TURN 3
    # =========================================================================
    player_3 = "I've heard rumors, Duke. Late night meetings. Whispered plans. Should I be concerned?"

    print_slow(f"{player_3}\n")

    response_3 = generate(f"""You are Duke Valerius in a medieval political intrigue game.

PERSONALITY: Calculating, cautious, formal. Values self-preservation above all.
HIDDEN STATE: Near panic, but years of court training keep you composed.
WHAT YOU KNOW:
- The King is directly accusing you of conspiracy
- If you admit anything, you'll share the Baron's fate
- You need to deflect, but denial may sound hollow
- Your only hope is to appear wounded by the accusation

PREVIOUS EXCHANGE:
King: "Please, sit. We have much to discuss. The Baron's betrayal weighs on me."
You: "{response_1}"
King: "You knew him well, didn't you? The Baron. You were... close."
You: "{response_2}"

THE KING NOW SAYS: "{player_3}"

Respond in character. 2-3 sentences. This is a critical moment.
You must express hurt/offense at the accusation while not overplaying it.
Physical details should show barely-controlled fear.
Output ONLY your dialogue and brief action.""")

    print_slow(f"""
  {response_3}

  > """)

    # =========================================================================
    # TURN 4 - THE DECISION
    # =========================================================================
    player_4 = "I have a letter, Duke. In the Baron's own hand. Your name appears... prominently."

    print_slow(f"{player_4}\n")

    response_4 = generate(f"""You are Duke Valerius in a medieval political intrigue game.

PERSONALITY: Calculating, cautious, formal. Values self-preservation above all.
HIDDEN STATE: The mask is cracking. You are caught. Fight or flight instincts war within you.
WHAT YOU KNOW:
- The King claims to have physical evidence
- This may be a bluff - or it may be real
- If real, denial is useless
- Your options: confess and beg mercy, deny and hope it's a bluff, or try to bargain

PREVIOUS EXCHANGE:
King: "Please, sit. We have much to discuss. The Baron's betrayal weighs on me."
You: "{response_1}"
King: "You knew him well, didn't you? The Baron. You were... close."
You: "{response_2}"
King: "I've heard rumors, Duke. Late night meetings. Whispered plans. Should I be concerned?"
You: "{response_3}"

THE KING NOW SAYS: "{player_4}"

Respond in character. 2-3 sentences. This is the breaking point.
Show visible fear now - hands trembling, voice faltering.
You must make a choice: crumble, deflect, or try to bargain.
Output ONLY your dialogue and brief action.""")

    print_slow(f"""
  {response_4}

  ─────────────────────────────────────────────────────────────────────

  [Continue interrogation]  [Call the guards]  [Offer mercy for information]

  > """)

    print_slow("""
╔══════════════════════════════════════════════════════════════════════╗
║                           END OF DEMO                                ║
╚══════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
