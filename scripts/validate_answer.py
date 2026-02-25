import os
import sys
import json
import subprocess
import re
from openai import OpenAI

def get_pr_comments(pr_number):
    """Fetch all comments for a PR using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/owner/repo/pulls/{pr_number}/comments'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch PR comments: {result.stderr}")
        
        comments = json.loads(result.stdout) if result.stdout else []
        return comments
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout fetching PR comments")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse PR comments JSON")

def get_pr_issue_comments(pr_number):
    """Fetch all issue comments (regular comments) for a PR using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/owner/repo/issues/{pr_number}/comments'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch issue comments: {result.stderr}")
        
        comments = json.loads(result.stdout) if result.stdout else []
        return comments
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout fetching issue comments")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse issue comments JSON")

def extract_answer_key(pr_number):
    """Extract the hidden answer key from Passmatic's initial comment."""
    try:
        comments = get_pr_issue_comments(pr_number)
        
        for comment in comments:
            if 'PASSMATIC_ANSWER:' in comment.get('body', ''):
                body = comment['body']
                match = re.search(r'<!--\s*PASSMATIC_ANSWER:(.*?)\s*-->', body, re.DOTALL)
                if match:
                    return match.group(1).strip()
        
        raise ValueError("No Passmatic answer key found in PR comments")
    except Exception as e:
        raise RuntimeError(f"Failed to extract answer key: {str(e)}")

def validate_answer_with_llm(question, correct_answer, user_answer):
    """Use LLM to grade the user's answer against the correct answer."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    api_base = os.environ.get('OPENAI_API_BASE', 'https://api.z.ai/api/coding/paas/v4')
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    prompt = f"""You are a strict technical reviewer. Evaluate if the user's answer demonstrates correct understanding of the code changes.

Question: {question}

Expected Answer (reference): {correct_answer}

User's Answer: {user_answer}

Evaluate based on:
1. Technical accuracy of the explanation
2. Understanding of the core concepts
3. Relevance to the question asked

Respond with JSON in this exact format:
{{
    "passed": true/false,
    "feedback": "Brief feedback message (1-2 sentences)"
}}"""
    
    try:
        response = client.chat.completions.create(
            model="glm-5",
            messages=[
                {"role": "system", "content": "You are a fair but strict technical reviewer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            timeout=60
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        if 'passed' not in result or 'feedback' not in result:
            raise ValueError("Invalid LLM response format")
        
        return result['passed'], result['feedback']
    except Exception as e:
        raise RuntimeError(f"Failed to validate answer: {str(e)}")

def get_question_from_comment(pr_number):
    """Extract the question from Passmatic's initial comment."""
    try:
        comments = get_pr_issue_comments(pr_number)
        
        for comment in comments:
            body = comment.get('body', '')
            if 'Passmatic: Vibe Check Required' in body:
                match = re.search(r'### Question:\s*\n(.*?)(?:\n-{{3,}}|\n##)', body, re.DOTALL)
                if match:
                    return match.group(1).strip()
        
        raise ValueError("No Passmatic question found in PR comments")
    except Exception as e:
        raise RuntimeError(f"Failed to extract question: {str(e)}")

def post_success_comment(pr_number):
    """Post a success comment on the PR."""
    comment_body = """## ✅ Passmatic: Vibe Check Passed!

**The vibe is informed.** You've demonstrated understanding of your changes. This PR is now approved and ready for merge.

🎉 Great work!"""
    
    subprocess.run(
        ['gh', 'pr', 'comment', pr_number, '--body', comment_body],
        capture_output=True,
        timeout=30
    )

def post_failure_comment(pr_number, feedback):
    """Post a failure comment with feedback."""
    comment_body = f"""## ❌ Passmatic: Vibe Check Failed

Your answer doesn't quite demonstrate full understanding of the changes.

**Feedback:** {feedback}

Please try again by responding with:
```
!answer <your revised answer>
```

Take a moment to review the technical details of your changes."""
    
    subprocess.run(
        ['gh', 'pr', 'comment', pr_number, '--body', comment_body],
        capture_output=True,
        timeout=30
    )

def add_reaction_to_comment(pr_number, comment_id, emoji):
    """Add a reaction emoji to a comment."""
    subprocess.run(
        ['gh', 'api', 
         f'repos/owner/repo/issues/comments/{comment_id}/reactions',
         '--method', 'POST',
         '-f', f'content={emoji}'],
        capture_output=True,
        timeout=30
    )

def approve_pr(pr_number):
    """Approve the PR for merging."""
    result = subprocess.run(
        ['gh', 'pr', 'review', pr_number, '--approve', '--body', '✅ Passmatic: Approved'],
        capture_output=True,
        timeout=30
    )
    return result.returncode == 0

def main():
    try:
        # Parse inputs from environment
        pr_number = os.environ.get('PR_NUMBER')
        comment_body = os.environ.get('COMMENT_BODY', '')
        comment_id = os.environ.get('COMMENT_ID')
        pr_author = os.environ.get('PR_AUTHOR')
        comment_author = os.environ.get('COMMENT_AUTHOR')
        
        if not pr_number:
            raise ValueError("PR_NUMBER environment variable not set")
        
        print(f"🔍 Validating vibe check for PR #{pr_number}...")
        
        # Check if comment starts with !answer
        if not comment_body.strip().startswith('!answer'):
            print("⏭️  Skipping: Comment does not start with !answer")
            sys.exit(0)
        
        # Extract user's answer
        user_answer = comment_body.replace('!answer', '', 1).strip()
        if not user_answer:
            print("❌ Error: Answer cannot be empty")
            sys.exit(1)
        
        print(f"📝 Answer received: {user_answer[:50]}...")
        
        # Get question and correct answer from PR comments
        print("🔎 Retrieving question and answer key...")
        question = get_question_from_comment(pr_number)
        correct_answer = extract_answer_key(pr_number)
        
        # Validate answer using LLM
        print("🤖 Validating answer...")
        passed, feedback = validate_answer_with_llm(question, correct_answer, user_answer)
        
        if passed:
            print("✅ Answer validated successfully")
            approve_pr(pr_number)
            post_success_comment(pr_number)
            if comment_id:
                add_reaction_to_comment(pr_number, comment_id, '+1')
            sys.exit(0)
        else:
            print(f"❌ Answer validation failed: {feedback}")
            post_failure_comment(pr_number, feedback)
            if comment_id:
                add_reaction_to_comment(pr_number, comment_id, '-1')
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
