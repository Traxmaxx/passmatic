# Passmatic 🔐

**The only vibe that passes is an informed one.**

Passmatic is a GitHub Action that enforces a "Vibe Check" on Pull Requests. It prevents PRs from being merged until the author successfully answers a question proving they understand the code changes they're proposing.

## Features

- 🤖 **AI-Powered Questions**: Generates technical questions based on actual code diffs using LLM
- 🔄 **Stateless**: Uses PR comment thread as the database
- 👥 **Collaborator-Only**: Only repository collaborators can trigger Passmatic

## Setup

### 1. Add Secrets

Go to Settings → Secrets and variables → Actions and add:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.z.ai/api/coding/paas/v4
```

### 2. Copy Files

Copy to your repository:
```
.github/workflows/passmatic-quiz.yml
.github/workflows/passmatic-validate.yml
scripts/generate_question.py
scripts/system_prompt.txt
scripts/validate_answer.py
requirements.txt
```

### 3. Configure Branch Protection

Require status check: "Passmatic - The Interrogator / 🔍 Vibe Check"

### 4. Add Collaborators

Add users as collaborators in Settings → Collaborators and teams

## Usage

When you open a PR:
1. Passmatic analyzes your diff and generates a question
2. Respond with:
```
!answer Your detailed explanation of the changes
```
3. Passmatic validates and approves or provides feedback

## Troubleshooting

- **Workflow not triggering**: Check Actions settings and verify collaborator status
- **API timeout**: Increase `timeout-minutes` or verify API key
- **Validation fails**: Provide detailed, specific answers
