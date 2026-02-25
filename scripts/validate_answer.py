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

def extract_answer_keys(pr_number):
    """Extract the hidden answer keys from Passmatic's initial comment."""
    try:
        comments = get_pr_issue_comments(pr_number)
        
        for comment in comments:
            if 'PASSMATIC_ANSWER_1:' in comment.get('body', ''):
                body = comment['body']
                answers = {}
                for i in range(1, 4):
                    match = re.search(rf'<!--\s*PASSMATIC_ANSWER_{i}:(.*?)\s*-->', body, re.DOTALL)
                    if match:
                        answers[i] = match.group(1).strip()
                
                if len(answers) == 3:
                    return answers
        
        raise ValueError("No Passmatic answer keys found in PR comments")
    except Exception as e:
        raise RuntimeError(f"Failed to extract answer keys: {str(e)}")

def validate_answer_with_llm(question, correct_answer, user_answer):
    """Use LLM to grade the user's answer against the correct answer."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    api_base = os.environ.get('OPENAI_API_BASE', 'https://api.z.ai/api/coding/paas/v4')
    model = os.environ.get('OPENAI_MODEL', 'glm-4.7')
    
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
            model=model,
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

def get_questions_from_comment(pr_number):
    """Extract the questions from Passmatic's initial comment."""
    try:
        comments = get_pr_issue_comments(pr_number)
        
        for comment in comments:
            body = comment.get('body', '')
            if 'Passmatic: Vibe Check Required' in body:
                questions = {}
                for i in range(1, 4):
                    match = re.search(rf'### Question {i}:\s*\n(.*?)(?=### Question|$)', body, re.DOTALL)
                    if match:
                        questions[i] = match.group(1).strip()
                
                if len(questions) == 3:
                    return questions
        
        raise ValueError("No Passmatic questions found in PR comments")
    except Exception as e:
        raise RuntimeError(f"Failed to extract questions: {str(e)}")

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

Some of your answers don't quite demonstrate full understanding of the changes.

{feedback}

Please try again by responding with:
```
!answer
1. Your revised answer to question 1
2. Your revised answer to question 2
3. Your revised answer to question 3
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
        
        # Extract user's answers (numbered 1, 2, 3)
        user_answer = comment_body.replace('!answer', '', 1).strip()
        if not user_answer:
            print("❌ Error: Answer cannot be empty")
            sys.exit(1)
        
        # Parse numbered answers
        user_answers = {}
        lines = user_answer.split('\n')
        current_answer = ""
        current_number = None
        
        for line in lines:
            # Check for numbered answer (e.g., "1.", "2.", "3.")
            match = re.match(r'^\s*(\d+)\.\s*', line)
            if match:
                num = int(match.group(1))
                if 1 <= num <= 3:
                    if current_number is not None:
                        user_answers[current_number] = current_answer.strip()
                    current_number = num
                    current_answer = line[match.end():]
            elif current_number is not None:
                current_answer += '\n' + line
        
        # Save last answer
        if current_number is not None and current_answer:
            user_answers[current_number] = current_answer.strip()
        
        # Check if we have 3 answers
        if len(user_answers) != 3:
            print(f"❌ Error: Expected 3 answers, got {len(user_answers)}. Please format your answers as:")
            print("``")
            print("!answer")
            print("1. Your answer to question 1")
            print("2. Your answer to question 2")
            print("3. Your answer to question 3")
            print("```")
            sys.exit(1)
        
        print(f"📝 {len(user_answers)} answers received")
        
        # Get questions and correct answers from PR comments
        print("🔎 Retrieving questions and answer keys...")
        questions = get_questions_from_comment(pr_number)
        correct_answers = extract_answer_keys(pr_number)
        
        # Validate each answer
        print("🤖 Validating answers...")
        results = []
        for i in range(1, 4):
            print(f"  Validating answer {i}...")
            passed, feedback = validate_answer_with_llm(
                questions[i],
                correct_answers[i],
                user_answers[i]
            )
            results.append({
                'number': i,
                'passed': passed,
                'feedback': feedback
            })
        
        # Check if all answers passed
        all_passed = all(r['passed'] for r in results)
        
        if all_passed:
            print("✅ All answers validated successfully")
            approve_pr(pr_number)
            post_success_comment(pr_number)
            if comment_id:
                add_reaction_to_comment(pr_number, comment_id, '+1')
            sys.exit(0)
        else:
            failed_answers = [r for r in results if not r['passed']]
            print(f"❌ {len(failed_answers)} answer(s) validation failed")
            
            # Build detailed feedback
            feedback_lines = []
            for r in results:
                if not r['passed']:
                    feedback_lines.append(f"**Question {r['number']}**: {r['feedback']}")
            
            feedback_text = "\n\n".join(feedback_lines)
            post_failure_comment(pr_number, feedback_text)
            if comment_id:
                add_reaction_to_comment(pr_number, comment_id, '-1')
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
