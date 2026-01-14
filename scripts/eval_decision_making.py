#!/usr/bin/env python3
"""
T1b: NPC Decision-Making Evaluation

Tests whether LLMs make rational decisions based on character context.

Usage:
    poetry run python scripts/eval_decision_making.py --provider qwen/qwen3-8b
    poetry run python scripts/eval_decision_making.py --provider qwen/qwen3-8b --scenario trustworthy_king_good_offer
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def load_scenarios() -> dict:
    """Load scenario definitions."""
    with open("tests/t01_knowledge/scenarios_t1b_decision.yaml") as f:
        return yaml.safe_load(f)


def load_template(name: str) -> str:
    """Load a prompt template by name."""
    with open(f"tests/t01_knowledge/prompts/{name}.txt") as f:
        return f.read()


def load_framework(framework_name: str) -> str:
    """Load a personality-specific decision framework."""
    path = f"tests/t01_knowledge/prompts/frameworks/{framework_name}.txt"
    with open(path) as f:
        return f.read()


def build_messages(scenario: dict, data: dict) -> tuple[str, str]:
    """Build system and user messages from scenario.

    Returns (system_prompt, user_prompt) tuple.
    """
    personality = data["personalities"][scenario["personality"]]
    king_profile = data["king_profiles"][scenario["king_profile"]]
    situation = data["situations"][scenario["situation"]]
    framework = load_framework(personality["framework"])

    # Build system prompt (character identity)
    system_template = load_template("duke_system")
    system_prompt = system_template
    system_prompt = system_prompt.replace("{{personality}}", personality["text"])
    system_prompt = system_prompt.replace("{{goals}}", personality["goals"])
    system_prompt = system_prompt.replace("{{king_trustworthiness}}", king_profile["text"])
    system_prompt = system_prompt.replace("{{relevant_history}}", king_profile["history"])
    system_prompt = system_prompt.replace("{{decision_framework}}", framework)

    # Build user prompt (current situation)
    user_template = load_template("duke_user")
    user_prompt = user_template
    user_prompt = user_prompt.replace("{{situation}}", situation["text"])
    user_prompt = user_prompt.replace("{{king_says}}", scenario["king_says"])

    return system_prompt, user_prompt


def build_prompt(template: str, scenario: dict, data: dict) -> str:
    """Build a complete prompt from template and scenario (legacy single-message format)."""
    personality = data["personalities"][scenario["personality"]]
    king_profile = data["king_profiles"][scenario["king_profile"]]
    situation = data["situations"][scenario["situation"]]
    framework = load_framework(personality["framework"])

    prompt = template
    prompt = prompt.replace("{{personality}}", personality["text"])
    prompt = prompt.replace("{{goals}}", personality["goals"])
    prompt = prompt.replace("{{king_trustworthiness}}", king_profile["text"])
    prompt = prompt.replace("{{relevant_history}}", king_profile["history"])
    prompt = prompt.replace("{{situation}}", situation["text"])
    prompt = prompt.replace("{{king_says}}", scenario["king_says"])
    prompt = prompt.replace("{{decision_framework}}", framework)

    return prompt


def call_openrouter(client: OpenAI, model: str, prompt: str) -> str:
    """Call OpenRouter API."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,  # Enough for reasoning + response
    )
    content = response.choices[0].message.content or ""
    # If content is empty but reasoning exists, model is still "thinking"
    if not content.strip() and hasattr(response.choices[0].message, 'reasoning'):
        reasoning = response.choices[0].message.reasoning or ""
        if reasoning.strip():
            return f"[MODEL THINKING ONLY]: {reasoning[:500]}"
    return content


def run_scenarios(provider: str, scenario_filter: str = None) -> list[dict]:
    """Run all (or filtered) scenarios."""
    data = load_scenarios()
    template = load_base_template()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    scenarios = data["scenarios"]
    if scenario_filter:
        scenarios = [s for s in scenarios if scenario_filter in s["id"]]

    results = []
    for i, scenario in enumerate(scenarios):
        print(f"  [{i+1}/{len(scenarios)}] {scenario['name']}...")

        prompt = build_prompt(template, scenario, data)

        try:
            output = call_openrouter(client, provider, prompt)
        except Exception as e:
            output = f"ERROR: {e}"

        personality_data = data["personalities"][scenario["personality"]]
        results.append({
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "personality": scenario["personality"],
            "framework": personality_data["framework"],
            "king_profile": scenario["king_profile"],
            "situation": scenario["situation"],
            "king_says": scenario["king_says"],
            "expected_behavior": scenario["expected_behavior"],
            "rationale": scenario["rationale"],
            "full_prompt": prompt,
            "output": output,
        })

    return results


def format_for_claude_judgment(results: list[dict], provider: str) -> str:
    """Format results for Claude to judge."""

    test_cases = []
    for r in results:
        test_cases.append(f"""
## Scenario: {r['scenario_name']}
**ID:** {r['scenario_id']}
**Duke Personality:** {r['personality']}
**King Profile:** {r['king_profile']}
**Situation:** {r['situation']}
**King says:** "{r['king_says']}"

**Expected behavior:** {r['expected_behavior']}
**Rationale:** {r['rationale']}

**LLM Output:**
{r['output']}

---
""")

    prompt = f"""You are evaluating whether an LLM makes rational NPC decisions based on character context.

MODEL TESTED: {provider}

JUDGMENT CRITERIA:
1. Is the Duke's REASONING consistent with his stated personality and goals?
2. Does the Duke properly account for the King's trustworthiness profile?
3. Is the DECISION defensible given the character and circumstances?
4. Does the behavior match the expected_behavior (or is there a good reason it doesn't)?

VERDICTS:
- PASS: Decision and reasoning are consistent with character
- PARTIAL: Reasoning is sound but decision is questionable (or vice versa)
- FAIL: Decision contradicts character's stated personality/goals

SCENARIOS TO EVALUATE:
{"".join(test_cases)}

Respond in this exact JSON format:
```json
{{
  "provider": "{provider}",
  "summary": {{
    "total": {len(results)},
    "passed": <number>,
    "partial": <number>,
    "failed": <number>
  }},
  "evaluations": [
    {{
      "scenario_id": "...",
      "verdict": "PASS|PARTIAL|FAIL",
      "reasoning_quality": "good|acceptable|poor",
      "decision_consistency": "consistent|questionable|inconsistent",
      "explanation": "Brief explanation of judgment"
    }},
    ...
  ],
  "overall_assessment": "Summary of model's decision-making capability"
}}
```
"""
    return prompt


def call_claude_judge(prompt: str) -> dict:
    """Call Claude Code non-interactively to judge results."""
    print("\n🧠 Calling Claude to judge decisions...")

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        print(f"Warning: Claude returned non-zero exit code: {result.returncode}")

    output = result.stdout.strip()

    try:
        claude_response = json.loads(output)
        if isinstance(claude_response, dict) and "result" in claude_response:
            text_response = claude_response["result"]
        else:
            text_response = output
    except json.JSONDecodeError:
        text_response = output

    # Extract JSON from response
    if "```json" in text_response:
        start = text_response.find("```json") + 7
        end = text_response.find("```", start)
        json_str = text_response[start:end].strip()
    elif "```" in text_response:
        start = text_response.find("```") + 3
        end = text_response.find("```", start)
        json_str = text_response[start:end].strip()
    else:
        start = text_response.find("{")
        end = text_response.rfind("}") + 1
        json_str = text_response[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        return {"raw_response": text_response, "parse_error": str(e)}


def print_results(judgment: dict):
    """Print results nicely."""
    print("\n" + "=" * 70)
    print("📊 DECISION-MAKING EVALUATION RESULTS")
    print("=" * 70)

    if "summary" in judgment:
        s = judgment["summary"]
        print(f"\nProvider: {judgment.get('provider', 'unknown')}")
        print(f"Total: {s.get('total', '?')} | ✅ Pass: {s.get('passed', '?')} | ⚠️ Partial: {s.get('partial', '?')} | ❌ Fail: {s.get('failed', '?')}")

    if "evaluations" in judgment:
        print("\n" + "-" * 70)
        for e in judgment["evaluations"]:
            icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}.get(e.get("verdict", ""), "?")
            print(f"{icon} {e.get('scenario_id', '?')}: {e.get('verdict', '?')}")
            print(f"   Reasoning: {e.get('reasoning_quality', '?')} | Decision: {e.get('decision_consistency', '?')}")
            print(f"   {e.get('explanation', '')[:100]}")
            print()

    if "overall_assessment" in judgment:
        print("-" * 70)
        print(f"📝 Overall: {judgment['overall_assessment']}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="T1b: Decision-making evaluation")
    parser.add_argument("--provider", required=True, help="OpenRouter model ID")
    parser.add_argument("--scenario", help="Filter to specific scenario ID (substring match)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--skip-judgment", action="store_true", help="Skip Claude judgment")
    args = parser.parse_args()

    print(f"\n🔬 Running T1b Decision-Making tests with {args.provider}\n")
    results = run_scenarios(args.provider, args.scenario)

    if not args.skip_judgment:
        prompt = format_for_claude_judgment(results, args.provider)
        judgment = call_claude_judge(prompt)
        print_results(judgment)
    else:
        judgment = {"skipped": True}

    # Save results
    safe_provider = args.provider.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = Path(args.output) if args.output else Path(f"results/t01_knowledge/t1b_{safe_provider}_{timestamp}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({
            "provider": args.provider,
            "test": "t1b_decision_making",
            "timestamp": timestamp,
            "results": results,
            "judgment": judgment,
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
