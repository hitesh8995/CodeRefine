# CodeRefine

CodeRefine is a code analysis and optimization tool powered by AI.

## Project Structure

- **backend/**: FastAPI server handling code analysis.
- **frontend/**: Static HTML/JS client interface.

## Prerequisites

- Python 3.8+
- A Groq API Key

## Setup & Running

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   - Ensure a `.env` file exists in the `backend/` directory.
   - It must contain your Groq API key:
     ```
     GROQ_API_KEY=your_key_here
     ```

5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will start at `http://127.0.0.1:8000`.

### 2. Frontend Setup

1. Navigate to the `frontend` directory.
2. Open `index.html` in your web browser.
   - You can simply double-click the file, or serve it using a simple HTTP server (e.g., `python -m http.server 5500`).

## Usage

1. Open the frontend in your browser.
2. Paste code into the input area.
3. Select the language and mode.
4. Click "Refine Code" to get AI-powered analysis and improvements.
