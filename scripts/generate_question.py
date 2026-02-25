import os
import sys
import json
import subprocess
import re
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

def generate_question_and_answer(diff):
    """Generate a technical question about the diff using LLM."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    api_base = os.environ.get('OPENAI_API_BASE', 'https://api.z.ai/api/coding/paas/v4')
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    prompt = f"""You are a senior code reviewer. Analyze this git diff and generate ONE technical question that tests the author's understanding of their changes.

Requirements:
- The question must be specific to the code changes
- Only someone who wrote/understands the changes should know the answer
- Focus on logic, implementation details, or design decisions
- Do NOT ask about formatting, style, or trivial changes

Diff:
{diff}

Respond with JSON in this exact format:
{{
    "question": "Your technical question here",
    "answer": "The correct answer (2-3 sentences explaining the key point)"
}}"""
    
    try:
        response = client.chat.completions.create(
            model="glm-5",
            messages=[
                {"role": "system", "content": "You are a strict code reviewer focused on technical understanding."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=60
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        if 'question' not in result or 'answer' not in result:
            raise ValueError("Invalid LLM response format")
        
        return result['question'], result['answer']
    except Exception as e:
        raise RuntimeError(f"Failed to generate question: {str(e)}")

def create_pr_comment(question, answer_key):
    """Create a PR comment with the question and hidden answer key."""
    pr_number = os.environ.get('PR_NUMBER')
    if not pr_number:
        raise ValueError("PR_NUMBER environment variable not set")
    
    # Hide answer key in HTML comment (not rendered by GitHub)
    hidden_answer = f"<!-- PASSMATIC_ANSWER:{answer_key} -->"
    
    comment_body = f"""## 🔐 Passmatic: Vibe Check Required

**The only vibe that passes is an informed one.**

Before this PR can be merged, please answer the following question to demonstrate your understanding of your changes:

---

### Question:
{question}

---

### How to respond:
Reply to this comment with:
```
!answer <your answer here>
```

Take your time to explain the technical details of your changes.
{hidden_answer}"""
    
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
        
        print("🤖 Generating question...")
        question, answer = generate_question_and_answer(diff)
        print(f"✓ Question generated: {question[:50]}...")
        
        print("📝 Posting vibe check...")
        create_pr_comment(question, answer)
        
        print("✅ Passmatic interrogator completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
