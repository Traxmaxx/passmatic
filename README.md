# Passmatic 🔐

**The only vibe that passes is an informed one.**

Passmatic is a GitHub Action that enforces a "Vibe Check" on Pull Requests. It prevents PRs from being merged until the author successfully answers a question proving they understand the code changes they're proposing.

---

**🤖 LLM-Coded Note:** This application itself was developed with the assistance of an LLM. It uses AI to verify that humans understand their code changes—a meta use of AI to ensure human understanding of code.

---

- 🤖 **AI-Powered Questions**: Generates technical questions based on actual code diffs using LLM
- 🔒 **Secure Design**: Answer keys hidden in HTML comments, never exposed in logs
- 🔄 **Stateless**: Uses PR comment thread as the database
- ⚡ **Resilient**: Handles API failures gracefully with proper timeouts
- 🎯 **Focused**: Validates understanding, not just syntax or formatting

## Architecture

Two-serverless GitHub workflows using the Split-Workflow Pattern:

### Workflow 1: The Interrogator (`passmatic-quiz.yml`)
- **Trigger**: PR opened/synchronized/reopened
- Fetches the git diff using GitHub CLI
- Calls LLM API to generate a specific technical question
- Posts a comment with the question and hidden answer key

### Workflow 2: The Validator (`passmatic-validate.yml`)
- **Trigger**: PR comment created
- Filters for `!answer` commands from PR author only
- Retrieves the hidden answer key from PR comments
- Uses LLM to grade the user's response
- Approves the PR or provides feedback

## Setup

### 1. Add Secrets to Repository

Go to your repository Settings → Secrets and variables → Actions and add:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.z.ai/api/coding/paas/v4
```

### 2. Copy Files

Copy the following files to your repository:

```
.github/
  workflows/
    passmatic-quiz.yml
    passmatic-validate.yml
scripts/
  generate_question.py
  validate_answer.py
requirements.txt
```

### 3. Configure Branch Protection

Add these branch protection rules to require Passmatic approval:

1. Go to Settings → Branches → Branch protection rules
2. Edit/add rule for your main branch
3. Require status checks to pass before merging
4. Select: "Passmatic - The Interrogator / 🔍 Vibe Check"

## Usage

When you open a PR:

1. **Passmatic triggers** and analyzes your diff
2. **Generates a question** about your specific changes
3. **Posts a comment** asking you to demonstrate understanding

You respond:

```
!answer Your detailed explanation of the changes
```

Passmatic validates your answer:

- ✅ **If correct**: Approves the PR for merging
- ❌ **If incorrect**: Provides feedback and asks you to try again

## Security Design

- Answer keys stored in HTML comments (`<!-- ANSWER:... -->`) - invisible in UI
- API keys injected via GitHub Secrets, masked in logs
- Only PR author can submit answers
- Stateless design - no external database required

## Environment Variables

Required secrets:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your LLM API key |
| `OPENAI_API_BASE` | LLM API endpoint (default: z.ai) |

## LLM Provider

Passmatic uses **z.ai GLM-5** as the default LLM provider via the Coding API endpoint. The integration is OpenAI-compatible, so you can easily switch to other providers by changing the `OPENAI_API_BASE` secret.

## Troubleshooting

### Workflow not triggering
- Ensure workflows are in `.github/workflows/` directory
- Check repository Actions settings are enabled

### API timeout errors
- Increase `timeout-minutes` in workflow files
- Check `OPENAI_API_KEY` is valid

### Answer validation fails
- Ensure your answer is detailed and specific
- Focus on technical implementation details
- Review the changes and try again with more detail

## License

MIT
