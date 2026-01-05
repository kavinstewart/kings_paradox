# The Crown's Paradox

> A "Pocket Paradox" King Simulator — where infinite player freedom meets iron consequences.

A text-based political intrigue game combining the open-ended input of Large Language Models with the rigid adjudication of a hard simulation layer. Type anything. The kingdom remembers everything.

## Vision

You are a Monarch navigating high-stakes vignettes: rebellions, betrayals, blackmail, and whispered conspiracies. Unlike typical AI games that devolve into "dream logic," The Crown's Paradox uses a **neuro-symbolic architecture** to ensure your lies have consequences, your secrets can leak, and your enemies actually remember what you did to them.

**Core Loop:**
```
Simulation triggers Vignette → Player types natural language →
LLM translates to game logic → Hard System updates world state →
Time jumps → Consequences compound → Repeat
```

## Architecture

The game runs on three layers:

| Layer | Role | Technology |
|-------|------|------------|
| **Hard System** | Source of truth (stats, facts, relationships) | Deterministic Python |
| **Semantic Referee** | Parses player text into game actions | LLM + structured output |
| **Narrative Renderer** | Generates prose the player reads | LLM with state injection |

The LLM cannot edit game state directly — it can only *request* updates via function calls that the Hard System validates.

## Current Status: Technical Risk Assessment

Before building the full game, we're validating whether the core architecture actually works. This repo contains **10 technical risk tests** that must pass before development proceeds.

### The Tests

| ID | Risk | Question |
|----|------|----------|
| T1 | Knowledge Boundaries | Can NPCs know secrets without leaking them? |
| T2 | State Consistency | Does the LLM respect established facts? |
| T3 | Rumor Mutation | Can we track rumors as they mutate across the court? |
| T4 | Telephone Consistency | Do secrets survive multi-NPC retelling? |
| T5 | Narrative Bridging | Can we generate coherent history from stat changes? |
| T6 | Selective Memory | Do NPCs surface memories at the right moments? |
| T7 | Vignette Orchestration | Can multiple triggers resolve without chaos? |
| T8 | Long-Context Retrieval | Can we find old facts when they matter? |
| T9 | Justified-Killing | Do NPCs form coherent opinions on executions? |
| T10 | Conspiracy Detection | Are plots detectable but not obvious? |

See [`docs/technical-prototype.md`](docs/technical-prototype.md) for full test specifications.

## Getting Started

### Prerequisites

- Python 3.11-3.13
- [Poetry](https://python-poetry.org/) for dependency management
- OpenAI and/or Anthropic API keys
- (Optional) Node.js for [Promptfoo](https://promptfoo.dev/) test harness

### Installation

```bash
# Clone the repository
git clone https://github.com/kavinstewart/kings_paradox.git
cd kings_paradox

# Install dependencies
poetry install

# Copy environment template and add your API keys
cp .env.example .env
# Edit .env with your API keys

# (Optional) Install promptfoo for evaluation harness
npm install -g promptfoo
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test suite
poetry run pytest tests/t01_knowledge/

# Run with verbose output
poetry run pytest -v --tb=short
```

## Project Structure

```
kings_paradox/
├── docs/
│   ├── game-concept.md          # Full game design document
│   └── technical-prototype.md   # Technical risk test specifications
├── src/kings_paradox/
│   ├── core/                    # Hard System (state, facts, ledger)
│   ├── npcs/                    # NPC models and behavior
│   ├── vignettes/               # Event triggering and orchestration
│   ├── information/             # Rumor tracking, grapevine graph
│   └── evaluation/              # LLM-as-judge scorers
├── tests/
│   ├── t01_knowledge/           # Knowledge boundary tests
│   ├── t02_consistency/         # State consistency tests
│   ├── ...                      # One directory per technical risk
│   └── conftest.py              # Shared pytest fixtures
├── pyproject.toml               # Poetry configuration
└── README.md
```

## Tech Stack

- **[DSPy](https://dspy.ai/)** — Prompt optimization and few-shot bootstrapping
- **[GEPA](https://github.com/gepa-ai/gepa)** — Reflective prompt evolution (included via DSPy)
- **[Promptfoo](https://promptfoo.dev/)** — Test harness and red-teaming
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation and game state models
- **OpenAI / Anthropic** — LLM providers

## Design Documents

- **[Game Concept](docs/game-concept.md)** — Full vision, mechanics, and anti-cheese systems
- **[Technical Prototype](docs/technical-prototype.md)** — Test specifications with pass/fail criteria

## Development Approach

We're using an **iterative prompt refinement** workflow:

1. **Baseline** — Write initial prompts, establish pass rates
2. **Failure Analysis** — Categorize systematic vs. probabilistic failures
3. **Optimization** — Apply DSPy/GEPA to refine prompts
4. **Adversarial Testing** — Use Promptfoo red-teaming to find edge cases
5. **Repeat** — Until pass criteria met or architecture pivot required

## Contributing

This is currently a solo project in the technical validation phase. Once the core architecture is proven, contribution guidelines will be added.

## License

TBD

---

*"The crown weighs heavy, but not as heavy as the secrets it keeps."*
