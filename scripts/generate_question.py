import os
import sys
import json
import subprocess
import re
from pathlib import Path
from openai import OpenAI

def get_pr_diff():
    """Fetch the git diff for the current PR using gh CLI."""
    try:
        pr_number = os.environ.get('PR_NUMBER')
        if not pr_number:
            raise ValueError("PR_NUMBER environment variable not set")

        result = subprocess.run(
            ['gh', 'pr', 'diff', pr_number],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch PR diff: {result.stderr}")
        
        diff = result.stdout
        if not diff or len(diff) < 50:
            raise ValueError("PR diff is too small or empty")
        
        return diff
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout fetching PR diff")
    except FileNotFoundError:
        raise RuntimeError("GitHub CLI (gh) not found")

def load_system_prompt():
    """Load the system prompt from file."""
    script_dir = Path(__file__).parent
    prompt_file = script_dir / "system_prompt.txt"
    
    if not prompt_file.exists():
        raise RuntimeError("system_prompt.txt not found in scripts directory")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def generate_question_and_answer(diff):
    """Generate a technical question about the diff using LLM."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    api_base = os.environ.get('OPENAI_API_BASE', 'https://api.z.ai/api/coding/paas/v4')
    model = os.environ.get('OPENAI_MODEL', 'glm-4.7')
    
    system_prompt = load_system_prompt()
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    prompt = f"""Analyze this git diff:

{diff}

Follow the instructions in the system prompt carefully."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=60
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        if 'questions' not in result or not isinstance(result['questions'], list) or len(result['questions']) != 3:
            raise ValueError("Invalid LLM response format: expected 'questions' array with 3 items")
        
        for i, q in enumerate(result['questions']):
            if 'question' not in q or 'answer' not in q:
                raise ValueError(f"Invalid format for question {i+1}")
        
        return result['questions']
    except Exception as e:
        raise RuntimeError(f"Failed to generate questions: {str(e)}")

def create_pr_comment(questions):
    """Create a PR comment with the questions and hidden answer keys."""
    pr_number = os.environ.get('PR_NUMBER')
    if not pr_number:
        raise ValueError("PR_NUMBER environment variable not set")
    
    # Hide answer keys in HTML comments (not rendered by GitHub)
    hidden_answers = "\n".join([
        f"<!-- PASSMATIC_ANSWER_{i+1}:{q['answer']} -->"
        for i, q in enumerate(questions)
    ])
    
    questions_text = "\n\n".join([
        f"### Question {i+1}:\n{q['question']}"
        for i, q in enumerate(questions)
    ])
    
    comment_body = f"""## 🔐 Passmatic: Vibe Check Required

**The only vibe that passes is an informed one.**

Before this PR can be merged, please answer the following **3 questions** to demonstrate your understanding of your changes:

---

{questions_text}

---

### How to respond:
Reply to this comment with:
```
!answer
1. Your answer to question 1
2. Your answer to question 2
3. Your answer to question 3
```

Take your time to explain the technical details of your changes.
{hidden_answers}"""
    
    try:
        result = subprocess.run(
            ['gh', 'pr', 'comment', pr_number, '--body', comment_body],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to post comment: {result.stderr}")
        
        print("✓ Vibe check posted successfully")
        return result.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout posting comment")
    except FileNotFoundError:
        raise RuntimeError("GitHub CLI (gh) not found")

def main():
    try:
        print("🔍 Analyzing PR changes...")
        diff = get_pr_diff()
        print(f"✓ Diff fetched ({len(diff)} characters)")
        
        print("🤖 Generating questions...")
        questions = generate_question_and_answer(diff)
        print(f"✓ Generated {len(questions)} questions")
        
        print("📝 Posting vibe check...")
        create_pr_comment(questions)
        
        print("✅ Passmatic interrogator completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
