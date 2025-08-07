# Emergency Assistant (CrimeGuard)

This project is an AI-powered emergency assistant for Sri Lanka, featuring a FastAPI backend and a React frontend. It provides immediate, actionable guidance in emergency situations, including both text and voice chat capabilities.

---

## Project Structure

```
Chat_bot_FYP/
├── AI_backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── chat_router.py        
│   │   ├── langchain_utils.py    
│   │   └── voice_config.py       
│   ├── main.py                   
│   ├── requirements.txt      
│   ├── test_mongo_connection.py
│   └── .env                      
└── Frontend/                      
    ├── public/
    │   ├── favicon.png           
    │   └── index.html           
    ├── src/
    │   ├── @assets/             
    │   │   ├── Crimegurd.png    
    │   │   └── microphone.gif    
    │   ├── Css/
    │   │   ├── App.css          
    │   │   └── index.css        
    │   ├── App.tsx              
    │   ├── index.tsx            
    │   ├── images.d.ts          
    │   └── reportWebVitals.ts   
    ├── package.json             
    └── tsconfig.json            
```

### Key Components:

- **Backend (`AI_backend/`):**
  - FastAPI server with OpenAI integration
  - MongoDB connection for history storage
  - Voice processing with Whisper and gTTS
  - Environment-based configuration

- **Frontend (`Frontend/`):**
  - React TypeScript application
  - Real-time chat interface
  - Voice chat capabilities
  - Responsive design with custom styling

---

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+ & npm** (for frontend)
- **MongoDB** (for chat history storage)
  - MongoDB Atlas account or local MongoDB server
  - Connection string for database access

---

## Features

- Chatbot interface with real-time responses using OpenAI's GPT-3.5-turbo model
- Voice chat capability with speech-to-text and text-to-speech
- Memory retention across conversations using LangChain and LangGraph
- MongoDB integration for persistent chat history
- Separate handling for text and voice chat history
- Fast response times and improved reliability
- Multilingual support (English, Sinhala, Tamil)
- Dark/Light theme support
- Quick emergency action buttons for common scenarios:
  - Fire emergency
  - Break-in situations
  - Medical emergencies
  - Police assistance
- Responsive design with animated UI elements
- Visual feedback for voice recording status

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
   The project includes a `requirements.txt` file with all necessary dependencies:
   ```
   Then run:
   ```sh
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   - Create a `.env` file in `AI_backend/` with the following variables:
     ```env
     # OpenAI Configuration
     OPENAI_API_KEY=your_openai_api_key_here
     
     # Server Configuration
     PORT=8000
     HOST=0.0.0.0
     
     # Model Configuration
     MODEL_NAME=gpt-3.5-turbo     
     model=whisper-1              
     
     # Logging Configuration
     LOG_LEVEL=INFO
     
     # MongoDB Configuration
     MONGODB_URI=your_mongodb_connection_string
     MONGO_DB_NAME=User_History
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

- **API Keys:** You must obtain a valid `OPENAI_API_KEY` for the backend to function. This key is used for both chat (GPT-3.5-turbo) and voice transcription (Whisper) features.
- **Voice Processing:** The system uses:
  - OpenAI Whisper for speech-to-text conversion
  - Google TTS (gTTS) for text-to-speech generation
- **Database Integration:**
  - MongoDB for storing chat and voice interaction history
  - Separate collections for text (`chat_history`) and voice (`voice_history`) interactions
  - Automatic timestamp and message type tracking
- **Security Features:**
  - JWT-based authentication using python-jose
  - Password hashing with bcrypt
  - CORS protection for API endpoints
  - Rate limiting for API requests
- **Localization:**
  - Multi-language support with dynamic language switching
  - Translations for UI elements and emergency messages
  - Language-specific voice processing
- **UI/UX Features:**
  - Responsive design with mobile support
  - Theme switching (Dark/Light mode)
  - Visual feedback for voice recording
  - Emergency quick action buttons
  - Animated background elements
- **Dependencies:** If you add new Python packages, update `requirements.txt` accordingly.
- **Production:** For deployment, use production-ready servers (e.g., `uvicorn` with `--reload` off, or behind a reverse proxy).

---

## Troubleshooting

- If you encounter CORS issues, ensure both servers are running on allowed origins (see backend CORS config).
- For environment variable errors, double-check your `.env` file in the backend directory.
- For MongoDB connection issues:
  - Verify your MongoDB connection string is correct
  - Ensure your IP address is whitelisted in MongoDB Atlas
  - Check MongoDB service is running if using local installation
- For voice chat issues:
  - Ensure microphone permissions are granted in your browser
  - Check that both text and voice history are being saved in MongoDB

---

## License

This project is for educational and emergency assistance purposes only. 