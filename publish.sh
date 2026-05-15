#!/usr/bin/env bash
# Publish the study-paper skill to GitHub as pleyva2004/claude-skill-study-paper.
# Idempotent-ish: errors out if the repo already exists or git already initialized.

set -euo pipefail

REPO_NAME="claude-skill-study-paper"
DESCRIPTION="Claude Code skill that turns an AI/ML paper into 5 layered artifacts: interview prep, math deep dive, opinion capture, GitHub sandbox, and a research-ready LaTeX lit-review entry."
SKILL_DIR="$HOME/.claude/skills/study-paper"

# Pre-flight checks
command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not installed. See https://cli.github.com/"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git not installed."; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "ERROR: gh not authenticated. Run: gh auth login"; exit 1; }

cd "$SKILL_DIR"

if [ -d .git ]; then
  echo "git already initialized in $SKILL_DIR"
else
  git init -b main
  cat > .gitignore <<'EOF'
.DS_Store
*.swp
*.swo
publish.sh
EOF
  git add SKILL.md README.md stages/ templates/ .gitignore
  git commit -m "Initial commit: study-paper skill v1"
fi

echo "Creating GitHub repo $REPO_NAME (public)..."
gh repo create "$REPO_NAME" --public --source=. --push --description "$DESCRIPTION"

echo "Done."
gh repo view --web 2>/dev/null || gh repo view
