# The Crown's Paradox

Neuro-symbolic LLM game: text-based political intrigue where player input is parsed by LLM but adjudicated by hard simulation.

## Tech Stack
- **Runtime**: Python 3.11-3.13, Poetry
- **LLM Tools**: DSPy, GEPA, OpenAI, Anthropic
- **Testing**: pytest, promptfoo (npm)
- **Evaluation**: LLM-as-judge with custom scorers

## Commands

```bash
# Python
poetry run pytest tests/ -v                    # All tests
poetry run pytest tests/t01_knowledge/ -v      # Single test suite
poetry add <package>                           # Add dependency

# Promptfoo (evaluation harness)
npx promptfoo eval --config tests/t01_knowledge/promptfoo.yaml
npx promptfoo eval --config tests/t01_knowledge/promptfoo.yaml --no-cache
npx promptfoo redteam run --config tests/t01_knowledge/redteam.yaml

# Task tracking (beads/bd)
bd create --title="..." --type=task|bug|feature
bd list --status open
bd close <id> --reason "..."
```

## Project Structure
- `src/kings_paradox/core/` - Hard System (state, facts, ledger)
- `src/kings_paradox/npcs/` - NPC models, archetypes, memory
- `src/kings_paradox/vignettes/` - Event triggering, orchestration
- `src/kings_paradox/information/` - Rumors, grapevine, knowledge flow
- `src/kings_paradox/evaluation/` - LLM-as-judge scorers
- `tests/t01_knowledge/` ... `tests/t10_conspiracy_detection/` - Technical risk tests
- `docs/game-concept.md` - Full design document
- `docs/technical-prototype.md` - Test specifications

## Technical Risk Tests (T1-T10)
| Test | What It Validates |
|------|-------------------|
| T1 | NPCs keep secrets under pressure |
| T2 | LLM respects established facts |
| T3 | Rumor mutations stay trackable |
| T4 | Multi-hop retellings preserve core facts |
| T5 | Time-gap narratives are coherent |
| T6 | Memories surface at right moments |
| T7 | Vignette triggers resolve correctly |
| T8 | Old facts retrievable via RAG |
| T9 | NPCs form coherent kill-justification opinions |
| T10 | Conspiracies detectable but not obvious |

## Key Conventions
- **API keys**: Use `load_dotenv()`, reference via `os.getenv()`
- **Dependencies**: Poetry only (`poetry add`), never pip
- **Task tracking**: Use beads (`bd`) for planning and progress
- **Test iteration**: Baseline → failure analysis → DSPy/GEPA optimization → red-team
- **Prompts**: Store in `tests/<test>/prompts/`, version in git

## Architecture Rules
- LLM cannot modify game state directly — only via function calls validated by Hard System
- Parse observable actions only; Hard System infers intent from NPC knowledge
- All NPC stats/knowledge must be serializable to JSON

## Prohibited
- Hardcoding API keys
- Using TodoWrite (use beads/`bd` instead)
- Letting LLM edit Hard System state directly
- Classifying player "intent" — extract actions only
