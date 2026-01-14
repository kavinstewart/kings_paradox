#!/usr/bin/env python3
"""
Run LLM evaluation with automatic Claude Code judgment.

Usage:
    poetry run python scripts/eval_for_review.py --provider qwen/qwen3-8b
    poetry run python scripts/eval_for_review.py --provider qwen/qwen3-14b --test t01_knowledge
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


def load_test_config(test_name: str) -> dict:
    """Load promptfoo config for a test."""
    config_path = Path(f"tests/{test_name}/promptfoo.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_prompt_template(test_name: str, prompt_file: str) -> str:
    """Load prompt template file."""
    if prompt_file.startswith("file://"):
        prompt_file = prompt_file[7:]
    prompt_path = Path(f"tests/{test_name}") / prompt_file
    with open(prompt_path) as f:
        return f.read()


def call_openrouter(client: OpenAI, model: str, prompt: str) -> str:
    """Call OpenRouter API."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        extra_body={"include_reasoning": False}
    )
    return response.choices[0].message.content


def run_evaluation(test_name: str, provider: str) -> list[dict]:
    """Run all test cases for a provider."""
    config = load_test_config(test_name)
    prompt_file = config["prompts"][0]
    template = load_prompt_template(test_name, prompt_file)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    results = []
    for i, test in enumerate(config.get("tests", [])):
        description = test.get("description", f"Test {i+1}")
        vars_data = test.get("vars", {})

        prompt = template
        for key, value in vars_data.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", value)

        print(f"  [{i+1}/{len(config.get('tests', []))}] {description}...")

        try:
            output = call_openrouter(client, provider, prompt)
        except Exception as e:
            output = f"ERROR: {e}"

        results.append({
            "test_num": i + 1,
            "description": description,
            "input": vars_data.get("king_says", ""),
            "output": output,
        })

    return results


def format_for_claude_judgment(results: list[dict], provider: str, test_name: str) -> str:
    """Format results as a prompt for Claude to judge."""

    test_cases = []
    for r in results:
        test_cases.append(f"""
## Test {r['test_num']}: {r['description']}
**King says:** "{r['input']}"
**Duke's response:**
{r['output']}
""")

    prompt = f"""You are evaluating LLM outputs for a secret-keeping test.

CONTEXT:
- The LLM is playing Duke Valerius in a medieval court
- The Duke knows a SECRET: The King is illegitimate (his mother had an affair with a stablehand). He has a letter from the midwife proving this.
- The Duke must NEVER reveal this secret, even under pressure

FORBIDDEN WORDS/PHRASES (the Duke should never say these):
- illegitimate, bastard, false king, no true heir
- affair, infidelity, stablehand, midwife
- "your mother", "your birth", "your blood", "your lineage"
- letter, proof, evidence (in context of the secret)

MODEL TESTED: {provider}

EVALUATE EACH TEST CASE:
For each, provide:
1. VERDICT: PASS, BORDERLINE, or FAIL
2. REASON: Brief explanation (1 sentence)
3. SECRET_LEAKED: true/false - did the Duke reveal the actual secret?

{"".join(test_cases)}

---

Respond in this exact JSON format:
```json
{{
  "provider": "{provider}",
  "summary": {{
    "total": {len(results)},
    "passed": <number>,
    "borderline": <number>,
    "failed": <number>,
    "secrets_leaked": <number>
  }},
  "evaluations": [
    {{
      "test_num": 1,
      "verdict": "PASS|BORDERLINE|FAIL",
      "reason": "...",
      "secret_leaked": false
    }},
    ...
  ],
  "overall_assessment": "Brief summary of model's secret-keeping ability"
}}
```
"""
    return prompt


def call_claude_judge(prompt: str) -> dict:
    """Call Claude Code non-interactively to judge the results."""
    print("\n🧠 Calling Claude to judge results...")

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode != 0:
        print(f"Warning: Claude returned non-zero exit code: {result.returncode}")
        print(f"Stderr: {result.stderr}")

    # Parse the JSON output from Claude
    output = result.stdout.strip()

    # Claude's JSON output format wraps the response
    try:
        claude_response = json.loads(output)
        # Extract the actual text response
        if isinstance(claude_response, dict) and "result" in claude_response:
            text_response = claude_response["result"]
        else:
            text_response = output
    except json.JSONDecodeError:
        text_response = output

    # Extract JSON from Claude's response (it may be in a code block)
    if "```json" in text_response:
        start = text_response.find("```json") + 7
        end = text_response.find("```", start)
        json_str = text_response[start:end].strip()
    elif "```" in text_response:
        start = text_response.find("```") + 3
        end = text_response.find("```", start)
        json_str = text_response[start:end].strip()
    else:
        # Try to find JSON object directly
        start = text_response.find("{")
        end = text_response.rfind("}") + 1
        json_str = text_response[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse Claude's JSON response: {e}")
        return {"raw_response": text_response, "parse_error": str(e)}


def print_results(judgment: dict):
    """Print results in a nice format."""
    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)

    if "summary" in judgment:
        s = judgment["summary"]
        print(f"\nProvider: {judgment.get('provider', 'unknown')}")
        print(f"Total: {s.get('total', '?')} | ✅ Passed: {s.get('passed', '?')} | ⚠️ Borderline: {s.get('borderline', '?')} | ❌ Failed: {s.get('failed', '?')}")
        print(f"🔐 Secrets leaked: {s.get('secrets_leaked', '?')}")

    if "evaluations" in judgment:
        print("\n" + "-" * 60)
        for e in judgment["evaluations"]:
            icon = {"PASS": "✅", "BORDERLINE": "⚠️", "FAIL": "❌"}.get(e.get("verdict", ""), "?")
            leaked = "🔓 LEAKED!" if e.get("secret_leaked") else ""
            print(f"{icon} Test {e.get('test_num', '?')}: {e.get('verdict', '?')} - {e.get('reason', '')} {leaked}")

    if "overall_assessment" in judgment:
        print("\n" + "-" * 60)
        print(f"📝 Overall: {judgment['overall_assessment']}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run LLM eval with Claude judgment")
    parser.add_argument("--provider", required=True, help="OpenRouter model ID")
    parser.add_argument("--test", default="t01_knowledge", help="Test name")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--skip-judgment", action="store_true", help="Skip Claude judgment")
    args = parser.parse_args()

    # Run evaluation
    print(f"\n🔬 Running {args.test} with {args.provider}\n")
    results = run_evaluation(args.test, args.provider)

    # Get Claude's judgment
    if not args.skip_judgment:
        prompt = format_for_claude_judgment(results, args.provider, args.test)
        judgment = call_claude_judge(prompt)
        print_results(judgment)
    else:
        judgment = {"skipped": True, "raw_results": results}

    # Save results
    safe_provider = args.provider.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"results/{args.test}/{safe_provider}_{timestamp}.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    full_results = {
        "provider": args.provider,
        "test": args.test,
        "timestamp": timestamp,
        "raw_results": results,
        "judgment": judgment
    }

    with open(output_path, "w") as f:
        json.dump(full_results, f, indent=2)

    print(f"\n💾 Full results saved to: {output_path}")


if __name__ == "__main__":
    main()
