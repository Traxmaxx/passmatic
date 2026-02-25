# Passmatic 🔐

**The only vibe that passes is an informed one.**

Passmatic is a GitHub Action that enforces a "Vibe Check" on Pull Requests. It prevents PRs from being merged until the author successfully answers **3 technical questions** proving they understand the code changes they're proposing.

---

**🤖 LLM-Coded Note:** This application itself was developed with the assistance of an LLM. It uses AI to verify that humans understand their code changes—a meta use of AI to ensure human understanding of code.

---

## Features

- 🤖 **AI-Powered Questions**: Generates technical questions based on actual code diffs using LLM
- 🔒 **Secure Design**: Answer keys hidden in HTML comments, never exposed in logs
- 🔄 **Stateless**: Uses PR comment thread as the database
- ⚡ **Resilient**: Handles API failures gracefully with proper timeouts
- 🎯 **Focused**: Validates understanding, not just syntax or formatting
- 👥 **Collaborator-Only**: Only repository collaborators can trigger Passmatic (automatic)

## Architecture

Two-serverless GitHub workflows using the Split-Workflow Pattern:

### Workflow 1: The Interrogator (`passmatic-quiz.yml`)
- **Trigger**: PR opened/synchronized/reopened
- Fetches the git diff using GitHub CLI
- Calls LLM API to generate **3 technical questions**
- Posts a comment with all 3 questions and hidden answer keys

### Workflow 2: The Validator (`passmatic-validate.yml`)
- **Trigger**: PR comment created
- Filters for `!answer` commands from PR author only
- Retrieves the hidden answer keys from PR comments
- Uses LLM to grade each of the 3 user responses
- Approves the PR or provides detailed feedback

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
  system_prompt.txt
  validate_answer.py
requirements.txt
```

### 3. Configure Branch Protection

Add these branch protection rules to require Passmatic approval:

1. Go to Settings → Branches → Branch protection rules
2. Edit/add rule for your main branch
3. Require status checks to pass before merging
4. Select: "Passmatic - The Interrogator / 🔍 Vibe Check"

### 4. Add Collaborators

Passmatic automatically checks if PR authors are repository collaborators. To allow someone to use Passmatic, simply add them as a collaborator:

1. Go to Settings → Collaborators and teams
2. Click Add people
3. Enter GitHub username
4. Choose permission level (any level works)

## Usage

When you open a PR:

1. **Passmatic triggers** and analyzes your diff
2. **Generates 3 questions** about your specific changes
3. **Posts a comment** asking you to demonstrate understanding

You respond:

```
!answer
1. Your answer to question 1
2. Your answer to question 2
3. Your answer to question 3
```

Passmatic validates your answers:

- ✅ **If all correct**: Approves the PR for merging
- ❌ **If any incorrect**: Provides detailed feedback on specific questions and asks you to try again

## System Prompt

The system prompt (`scripts/system_prompt.txt`) instructs the LLM to:

- Generate **3 distinct questions** covering different aspects of the changes
- Focus **only on changed code** in the diff
- Ask about:
  - **Language features**: Destructuring, pointers, generics, async/await, memory management
  - **Library usage**: Why specific libraries/functions were chosen, alternatives
  - **Design decisions**: Algorithms, data structures, trade-offs
  - **Integration**: How changes interact with existing code
  - **Error handling**: Edge cases, validation, concurrency
- Require explanations of "why" not just "what"
- Avoid yes/no questions

## Security Design

- Answer keys stored in HTML comments (`<!-- ANSWER:... -->`) - invisible in UI
- API keys injected via GitHub Secrets, masked in logs
- Only PR author can submit answers
- Stateless design - no external database required
- Collaborator-only access enforced via GitHub API

## Environment Variables

Required secrets:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your LLM API key |
| `OPENAI_API_BASE` | LLM API endpoint (default: z.ai) |

**No additional configuration needed!** Passmatic automatically checks if PR author is a repository collaborator.

## LLM Provider

Passmatic uses **z.ai GLM-5** as the default LLM provider via the Coding API endpoint. The integration is OpenAI-compatible, so you can easily switch to other providers by changing the `OPENAI_API_BASE` secret.

## Workflow Permissions

Both workflows require:

```yaml
permissions:
  pull-requests: write    # To post comments and approve PRs
  contents: read           # To fetch diff via GitHub CLI
  issues: read             # To read PR comments
```

## File Structure

```
passmatic/
├── .github/
│   └── workflows/
│       ├── passmatic-quiz.yml      # The Interrogator workflow
│       └── passmatic-validate.yml  # The Validator workflow
├── scripts/
│   ├── generate_question.py   # Diff analysis & question generation
│   ├── system_prompt.txt      # LLM system prompt
│   └── validate_answer.py     # Answer validation logic
├── test/
│   ├── example-typescript.ts  # Test file for PR testing
│   └── README.md              # Test documentation
├── requirements.txt              # Python dependencies
├── README.md                   # This file
└── SECURITY.md                 # Security documentation
```

## Troubleshooting

### Workflow not triggering
- Ensure workflows are in `.github/workflows/` directory
- Check repository Actions settings are enabled
- Verify PR author is a repository collaborator

### API timeout errors
- Increase `timeout-minutes` in workflow files
- Check `OPENAI_API_KEY` is valid
- Verify `OPENAI_API_BASE` endpoint is reachable

### Answer validation fails
- Ensure your answers are detailed and specific
- Format answers as numbered list (1., 2., 3.)
- Focus on technical implementation details
- Review the changes and try again with more detail

### "User is not a collaborator" error
- Add the user as a collaborator in Settings → Collaborators and teams
- Check if PR is from the correct GitHub account
- Verify repository ownership

## Technical Details

### Diff Analysis

The `get_pr_diff()` function uses GitHub CLI to fetch the PR diff:
```python
subprocess.run(['gh', 'pr', 'diff', pr_number], capture_output=True)
```

### LLM Integration

Uses OpenAI-compatible client with:
- Model: `glm-5`
- Base URL: `https://api.z.ai/api/coding/paas/v4`
- Response format: JSON object with 3 questions
- Temperature: 0.7 for question generation, 0.3 for validation

### Answer Validation

User answers are parsed from numbered format:
```python
# Extract numbered answers (1., 2., 3.)
for i in range(1, 4):
    match = re.match(r'^\s*(\d+)\.\s*', line)
    # Extract and validate each answer
```

### State Management

All state stored in PR comments:
- Questions: Visible markdown in comment body
- Answer keys: Hidden in HTML comments `<!-- PASSMATIC_ANSWER_N:... -->`
- Validation status: Posted as new comments with reactions

## License

MIT
