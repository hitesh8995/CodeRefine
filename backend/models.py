from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CodeSubmission(BaseModel):
    source_code: str = Field(..., description="The source code to analyze")
    language: str = Field(..., description="Programming language of the source code")
    teaching_mode: str = Field("pro", description="Explanation style: 'beginner' or 'pro'")

class AnalysisResult(BaseModel):
    bugs: List[str] = Field(..., description="List of detected bugs")
    performance_issues: List[str] = Field(..., description="List of performance bottlenecks")
    security_vulnerabilities: List[str] = Field(..., description="List of security risks")
    best_practice_violations: List[str] = Field(..., description="List of coding standard violations")
    refactored_code: str = Field(..., description="Optimized and rewritten code")
    explanation: str = Field(..., description="Detailed explanation of changes and improvements")
    quality_score: int = Field(..., ge=0, le=100, description="Code quality score out of 100")
    estimated_time: str = Field(..., description="Estimated runtime (e.g. '0.02ms', '1s')")
    memory_estimate: str = Field(..., description="Estimated memory usage (e.g. '512KB')")
    complexity_score: int = Field(..., description="Estimated cyclomatic complexity")
    detected_language: Optional[str] = Field(None, description="Language detected by AI")
    language_mismatch: bool = Field(False, description="True if detected language differs from submitted language")
    confidence_score_bug: float = Field(..., description="Confidence in bug detection (0-100)")
    confidence_score_optimization: float = Field(..., description="Confidence in optimization (0-100)")
    learning_tips: List[str] = Field(..., description="Tips for improvement")
    quality_metrics: Dict[str, int] = Field(..., description="Scores for maintainability, security, etc.")
    generated_tests: str = Field(..., description="Auto-generated unit tests")
    generated_docs: str = Field(..., description="Auto-generated documentation")

class ExecutionRequest(BaseModel):
    source_code: str
    language: str
    inputs: str = ""

class ExecutionResult(BaseModel):
    output: str
    error: str = ""
