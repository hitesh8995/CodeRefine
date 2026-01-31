import os
from groq import Groq
from dotenv import load_dotenv
from models import AnalysisResult

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def calculate_complexity(source_code: str) -> int:
    # A simple heuristic for complexity: count branching keywords
    # This is a basic estimation, a real AST parser would be better for production
    complexity = 1
    branching_keywords = [
        'if', 'else', 'elif', 'for', 'while', 'switch', 'case', 'catch', 
        '?', '&&', '||', 'and', 'or', 'except', 'with'
    ]
    for word in source_code.split():
        if word in branching_keywords:
            complexity += 1
    return complexity

async def analyze_code_with_ai(source_code: str, language: str, teaching_mode: str = "pro") -> AnalysisResult:
    system_prompt = f"""You are 'CodeRefine', an elite AI code reviewer and optimizer. 
    Analyze the provided {language} code.
    
    TEACHING MODE: {teaching_mode.upper()}
    - If mode is 'BEGINNER': Explain core concepts simply, avoid jargon, and focus on 'how it works'.
    - If mode is 'PRO': Focus on performance, memory, architecture, and advanced patterns. Concise technical language.

    Return a strictly valid JSON response acting as an API. 
    The JSON must match this structure exactly:
    {{
        "bugs": ["Line 10: Potential IndexError", "Line 4: Variable not defined"],
        "performance_issues": ["Line 6: Inefficient loop"],
        "security_vulnerabilities": ["Line 12: SQL Injection risk"],
        "best_practice_violations": ["Line 1: Missing type hints"],
        "refactored_code": "The complete rewritten code string here",
        "explanation": "A concise summary of what was fixed and why.",
        "quality_score": 85,
        "estimated_time": "0.45ms",
        "memory_estimate": "512KB",
        "detected_language": "python",
        "language_mismatch": false,
        "confidence_score_bug": 92.5,
        "confidence_score_optimization": 88.0,
        "learning_tips": ["Use list comprehensions", "Always close files"],
        "quality_metrics": {{
            "maintainability": 80,
            "security": 90,
            "performance": 70,
            "readability": 85
        }},
        "generated_tests": "def test_example(): ...",
        "generated_docs": "# Documentation\\n\\n## Summary..."
    }}
    
    IMPORTANT: 
    - 'estimated_time': Estimate logical execution time (e.g., "0.02ms").
    - 'memory_estimate': Estimate peak memory usage (e.g., "1.2MB").
    - 'detected_language': Identify the programming language of the code.
    - 'language_mismatch': Set to true if 'detected_language' is fundamentally different from {language}. (e.g. submitted Java but code is Python).
    - 'confidence_score_bug': 0-100% confidence in your bug detection.
    - 'confidence_score_optimization': 0-100% confidence in your rewrite.
    - 'quality_metrics': 0-100 scores for specific pillars.
    - 'generated_tests': Create a comprehensive suite of unit tests (using standard lib like unittest/pytest/jest) for the *Refactored Code*.
    - 'generated_docs': Create professional markdown documentation including 'Summary', 'API Reference', and 'Usage Example'.
    - **Issue Lists**: ALWAYS prefix issues with "Line <number>: " if possible. Example: "Line 12: Invalid syntax". If line number is unknown, omit it.
    
    
    Do not add any markdown formatting (like ```json) outside the structure. Just the raw JSON.
    
    IMPORTANT: 
    - If there are NO bugs, return an empty list: "bugs": []
    - Do NOT return strings like "None found" or "No issues detected" inside the lists. Use empty lists.
    - Be practical. Do not nitpick on missing docstrings for very simple snippets unless requested.
    - Only flag "Potential IndexError" or type checks if the code is intended for production.
    """
    
    user_prompt = f"Code to analyze:\n\n{source_code}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2, # Low temperature for consistent JSON
            response_format={"type": "json_object"},
        )
        
        response_content = chat_completion.choices[0].message.content
        import json
        data = json.loads(response_content)
        
        # Calculate complexity locally for now (or could ask AI)
        complexity = calculate_complexity(source_code)
        
        return AnalysisResult(
            bugs=data.get("bugs", []),
            performance_issues=data.get("performance_issues", []),
            security_vulnerabilities=data.get("security_vulnerabilities", []),
            best_practice_violations=data.get("best_practice_violations", []),
            refactored_code=data.get("refactored_code", source_code),
            explanation=data.get("explanation", "Analysis complete."),
            quality_score=data.get("quality_score", 0),
            estimated_time=data.get("estimated_time", "Unknown"),
            memory_estimate=data.get("memory_estimate", "Unknown"),
            detected_language=data.get("detected_language", "Unknown"),
            language_mismatch=data.get("language_mismatch", False),
            confidence_score_bug=data.get("confidence_score_bug", 0.0),
            confidence_score_optimization=data.get("confidence_score_optimization", 0.0),
            learning_tips=data.get("learning_tips", []),
            quality_metrics=data.get("quality_metrics", {}),
            generated_tests=data.get("generated_tests", "# No tests generated"),
            generated_docs=data.get("generated_docs", "# No documentation generated"),
            complexity_score=complexity
        )
        
    except Exception as e:
        print(f"Error calling Groq: {e}")
        # Return a fallback error result
        return AnalysisResult(
            bugs=["Failed to analyze code via AI"],
            performance_issues=[],
            security_vulnerabilities=[],
            best_practice_violations=[],
            refactored_code=source_code,
            explanation=f"AI Service Error: {str(e)}",
            quality_score=0,
            estimated_time="N/A",
            memory_estimate="N/A",
            detected_language="Unknown",
            language_mismatch=False,
            confidence_score_bug=0.0,
            confidence_score_optimization=0.0,
            learning_tips=[],
            quality_metrics={},
            generated_tests="# Error generating tests",
            generated_docs="# Error generating docs",
            complexity_score=calculate_complexity(source_code)
        )
