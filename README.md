# Emergency Assistant (CrimeGuard)

This project is an AI-powered emergency assistant for Sri Lanka, featuring a FastAPI backend and a React frontend. It provides immediate, actionable guidance in emergency situations, including both text and voice chat capabilities.

---

## Project Structure

```
Chat_bot_FYP/
├── AI_backend/         # FastAPI backend (Python)
│   └── app/
├── Frontend/           # React frontend (TypeScript)
```

---

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+ & npm** (for frontend)

---

## Backend Setup (FastAPI)

1. **Navigate to the backend directory:**
   ```sh
   cd AI_backend
   ```

2. **Create and activate a virtual environment (recommended):**
   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   > **Note:** Create a `requirements.txt` file with the following (inferred from code):
   ```
   fastapi
   uvicorn
   python-dotenv
   langchain
   langchain_groq
   langgraph
   groq
   gtts
   ```
   Then run:
   ```sh
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   - Create a `.env` file in `AI_backend/` with the following variables:
     ```env
     GROQ_API_KEY=your_groq_api_key_here
     MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct  # or your preferred model
     LOG_LEVEL=INFO
     PORT=8000
     HOST=0.0.0.0
     ```

5. **Run the backend server:**
   ```sh
   python main.py
   ```
   The backend will be available at `http://localhost:8000` (or your configured host/port).

---

## Frontend Setup (React)

1. **Navigate to the frontend directory:**
   ```sh
   cd Frontend
   ```

2. **Install dependencies:**
   ```sh
   npm install
   ```

3. **Start the development server:**
   ```sh
   npm start
   ```
   The frontend will be available at `http://localhost:3000`.

---

## Usage

- Access the frontend in your browser at [http://localhost:3000](http://localhost:3000).
- The frontend communicates with the backend API endpoints at `/chat` and `/voice_chat`.
- Ensure both backend and frontend servers are running for full functionality.

---

## Notes

- **API Keys:** You must obtain a valid `GROQ_API_KEY` for the backend to function.
- **Dependencies:** If you add new Python packages, update `requirements.txt` accordingly.
- **Production:** For deployment, use production-ready servers (e.g., `uvicorn` with `--reload` off, or behind a reverse proxy).

---

## Troubleshooting

- If you encounter CORS issues, ensure both servers are running on allowed origins (see backend CORS config).
- For environment variable errors, double-check your `.env` file in the backend directory.

---

## License

This project is for educational and emergency assistance purposes only. 
