from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import CodeSubmission, AnalysisResult, ExecutionRequest, ExecutionResult
from services import analyze_code_with_ai

app = FastAPI(title="CodeRefine API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeRefine API. Use /analyze to optimize your code."}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_code(submission: CodeSubmission):
    if not submission.source_code:
        raise HTTPException(status_code=400, detail="Source code cannot be empty")
    
    result = await analyze_code_with_ai(submission.source_code, submission.language, submission.teaching_mode)
    return result

@app.post("/execute", response_model=ExecutionResult)
async def execute_code(request: ExecutionRequest):
    import subprocess
    import tempfile
    import os
    import httpx

    # Map language names to Piston API language identifiers
    piston_languages = {
        "c": "c",
        "cpp": "c++",
        "java": "java",
        "go": "go",
        "typescript": "typescript",
        "r": "r"
    }

    try:
        # Use local execution for Python and JavaScript
        if request.language == "python":
            # Create a temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(request.source_code)
                temp_filename = f.name
            
            # Execute
            try:
                process = subprocess.Popen(
                    ['python', temp_filename],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=request.inputs, timeout=5)
                return ExecutionResult(output=stdout, error=stderr)
            except subprocess.TimeoutExpired:
                process.kill()
                return ExecutionResult(output="", error="Execution Timed Out (5s limit)")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
        
        elif request.language == "javascript":
            # Requires node to be installed
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(request.source_code)
                temp_filename = f.name
                
            try:
                process = subprocess.Popen(
                    ['node', temp_filename],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=request.inputs, timeout=5)
                return ExecutionResult(output=stdout, error=stderr)
            except subprocess.TimeoutExpired:
                process.kill()
                return ExecutionResult(output="", error="Execution Timed Out (5s limit)")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

        # Use Piston API for compiled languages and others
        elif request.language in piston_languages:
            async with httpx.AsyncClient() as client:
                # Determine appropriate filename
                file_extensions = {
                    "c": "main.c",
                    "cpp": "main.cpp",
                    "java": "Main.java",
                    "go": "main.go",
                    "typescript": "main.ts",
                    "r": "main.r"
                }
                
                filename = file_extensions.get(request.language, "main.txt")
                
                piston_request = {
                    "language": piston_languages[request.language],
                    "version": "*",  # Use latest version
                    "files": [
                        {
                            "name": filename,
                            "content": request.source_code
                        }
                    ],
                    "stdin": request.inputs,
                    "compile_timeout": 10000,
                    "run_timeout": 5000
                }
                
                response = await client.post(
                    "https://emkc.org/api/v2/piston/execute",
                    json=piston_request,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    return ExecutionResult(output="", error=f"Piston API Error: {response.status_code}")
                
                result = response.json()
                
                # Piston returns run.stdout and run.stderr
                if "run" in result:
                    stdout = result["run"].get("stdout", "")
                    stderr = result["run"].get("stderr", "")
                    
                    # If compilation failed, it might be in compile.stderr
                    if "compile" in result and result["compile"].get("stderr"):
                        stderr = f"Compilation Error:\n{result['compile']['stderr']}\n{stderr}"
                    
                    return ExecutionResult(output=stdout, error=stderr)
                else:
                    return ExecutionResult(output="", error="Unexpected response from Piston API")

        else:
             return ExecutionResult(output="", error=f"Execution for {request.language} is not supported yet.")

    except Exception as e:
        return ExecutionResult(output="", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
