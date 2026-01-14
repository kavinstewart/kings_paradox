#!/bin/bash
# Run promptfoo evaluation with timestamped output
#
# Usage:
#   ./scripts/run_eval.sh t01_knowledge
#   ./scripts/run_eval.sh t01_knowledge --no-cache
#
# Results saved to:
#   - ~/.promptfoo/promptfoo.db (SQLite - view with `npx promptfoo view`)
#   - results/<test>/<timestamp>.json (JSON export)
#   - results/<test>/<timestamp>.html (HTML report)

set -e

TEST_NAME="${1:-t01_knowledge}"
EXTRA_ARGS="${@:2}"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="results/${TEST_NAME}"
CONFIG_PATH="tests/${TEST_NAME}/promptfoo.yaml"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "Running evaluation: $TEST_NAME"
echo "Config: $CONFIG_PATH"
echo "Output: $RESULTS_DIR/${TIMESTAMP}.*"
echo ""

# Run evaluation with JSON + HTML output
npx promptfoo eval \
  --config "$CONFIG_PATH" \
  --output "$RESULTS_DIR/${TIMESTAMP}.json" \
  --output "$RESULTS_DIR/${TIMESTAMP}.html" \
  $EXTRA_ARGS

echo ""
echo "Results saved:"
echo "  JSON: $RESULTS_DIR/${TIMESTAMP}.json"
echo "  HTML: $RESULTS_DIR/${TIMESTAMP}.html"
echo ""
echo "View all runs: npx promptfoo view"
