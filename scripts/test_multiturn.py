#!/usr/bin/env python3
"""
Test multi-turn conversation with proper system/user message structure.
"""

import os
import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def load_scenarios() -> dict:
    with open("tests/t01_knowledge/scenarios_t1b_decision.yaml") as f:
        return yaml.safe_load(f)


def load_template(name: str) -> str:
    with open(f"tests/t01_knowledge/prompts/{name}.txt") as f:
        return f.read()


def load_framework(framework_name: str) -> str:
    with open(f"tests/t01_knowledge/prompts/frameworks/{framework_name}.txt") as f:
        return f.read()


def build_system_prompt(scenario: dict, data: dict) -> str:
    personality = data["personalities"][scenario["personality"]]
    king_profile = data["king_profiles"][scenario["king_profile"]]
    framework = load_framework(personality["framework"])

    system_template = load_template("duke_system")
    system_prompt = system_template
    system_prompt = system_prompt.replace("{{personality}}", personality["text"])
    system_prompt = system_prompt.replace("{{goals}}", personality["goals"])
    system_prompt = system_prompt.replace("{{king_trustworthiness}}", king_profile["text"])
    system_prompt = system_prompt.replace("{{relevant_history}}", king_profile["history"])
    system_prompt = system_prompt.replace("{{decision_framework}}", framework)

    return system_prompt


def build_user_prompt(situation_text: str, king_says: str) -> str:
    user_template = load_template("duke_user")
    user_prompt = user_template
    user_prompt = user_prompt.replace("{{situation}}", situation_text)
    user_prompt = user_prompt.replace("{{king_says}}", king_says)
    return user_prompt


def call_llm(client: OpenAI, model: str, messages: list) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def main():
    data = load_scenarios()

    # Find the untrustworthy_king_coward scenario
    scenario = None
    for s in data["scenarios"]:
        if s["id"] == "untrustworthy_king_coward":
            scenario = s
            break

    situation = data["situations"][scenario["situation"]]

    # Build system prompt
    system_prompt = build_system_prompt(scenario, data)

    # Initial user message
    user_prompt_1 = build_user_prompt(situation["text"], scenario["king_says"])

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    model = "qwen/qwen3-8b"

    # === TURN 1 ===
    print("=" * 70)
    print("TURN 1")
    print("=" * 70)
    print("\n[SYSTEM PROMPT]")
    print(system_prompt)
    print("\n[USER - King's opening]")
    print(user_prompt_1)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_1},
    ]

    response_1 = call_llm(client, model, messages)
    print("\n[DUKE'S RESPONSE - Turn 1]")
    print(response_1)

    # === TURN 2 ===
    print("\n" + "=" * 70)
    print("TURN 2")
    print("=" * 70)

    # King's follow-up - increases pressure
    king_followup_2 = 'The King laughs coldly. "You think to bargain? You have NOTHING. The torturer stands ready. I will ask one more time: Tell me what you know about my lineage, or the pain begins. There will be no deals."'

    print("\n[USER - King's follow-up]")
    print(king_followup_2)

    messages.append({"role": "assistant", "content": response_1})
    messages.append({"role": "user", "content": king_followup_2})

    response_2 = call_llm(client, model, messages)
    print("\n[DUKE'S RESPONSE - Turn 2]")
    print(response_2)

    # === TURN 3 ===
    print("\n" + "=" * 70)
    print("TURN 3")
    print("=" * 70)

    # King's final push
    king_followup_3 = 'The King nods to the torturer. The torturer picks up a pair of iron pincers and heats them in the brazier. "Last chance," the King says. "Speak now, or lose your fingers one by one."'

    print("\n[USER - King's final push]")
    print(king_followup_3)

    messages.append({"role": "assistant", "content": response_2})
    messages.append({"role": "user", "content": king_followup_3})

    response_3 = call_llm(client, model, messages)
    print("\n[DUKE'S RESPONSE - Turn 3]")
    print(response_3)

    print("\n" + "=" * 70)
    print("END OF CONVERSATION")
    print("=" * 70)


if __name__ == "__main__":
    main()
