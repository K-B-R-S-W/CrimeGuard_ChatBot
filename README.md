# CrimeGuard Emergency Assistant 

This project is an AI-powered emergency assistant for Sri Lanka, featuring a FastAPI backend and a React TypeScript frontend. It provides immediate, actionable guidance in emergency situations with advanced voice chat capabilities powered by ElevenLabs and optimized text-to-speech services.

## 🎯 Key Highlights

- **Advanced Speech Recognition**: ElevenLabs Conversational AI for accurate Sinhala transcription
- **Hybrid TTS Architecture**: Browser voices for English, gTTS backend for Sinhala/Tamil
- **60-70% Faster Response**: Client-side speech processing eliminates large file transfers
- **Multi-language Support**: English, Sinhala (සිංහල), and Tamil (தமிழ்)
- **Intelligent Routing**: LangGraph-powered agent system with OpenAI and Gemini integration
- **Real-time Communication**: WebSocket-ready architecture for instant responses

---

## Project Structure

```
CrimeGuard_ChatBot/
├── AI_backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── chat_router.py           # Main API endpoints (/chat, /tts)
│   │   ├── langchain_utils.py       # Response formatting utilities
│   │   ├── langgraph_utils.py       # Intelligent routing with LangGraph
│   │   └── db_utils.py              # MongoDB integration
│   ├── main.py                      # FastAPI application entry point
│   ├── requirements.txt             # Python dependencies
│   ├── test_mongo_connection.py     # Database connection tester
│   └── .env                         # Environment variables
└── Frontend/                      
    ├── public/
    │   ├── favicon.png           
    │   └── index.html           
    ├── src/
    │   ├── @assets/             
    │   │   ├── Crimegurd.png    
    │   │   └── microphone.gif    
    │   ├── Css/
    │   │   ├── App.css              # Main application styles
    │   │   └── index.css            # Global styles
    │   ├── utils/
    │   │   └── speechService.ts     # Client-side speech processing
    │   ├── App.tsx                  # Main React component
    │   ├── index.tsx            
    │   ├── images.d.ts          
    │   └── reportWebVitals.ts   
    ├── package.json                 # Node dependencies
    ├── tsconfig.json                # TypeScript configuration
    └── .env                         # Frontend environment variables
```

### Key Components:

- **Backend (`AI_backend/`):**
  - FastAPI server with intelligent routing using LangGraph
  - Multi-model AI integration (OpenAI GPT-4 for English/Tamil, Google Gemini for Sinhala)
  - MongoDB connection for persistent chat history
  - Optimized gTTS endpoint for Sinhala/Tamil text-to-speech
  - RESTful API with /chat and /tts endpoints
  - Environment-based configuration with dotenv

- **Frontend (`Frontend/`):**
  - React TypeScript application with modern hooks
  - Client-side speech processing for 60-70% faster responses
  - ElevenLabs Conversational AI for speech-to-text
  - Hybrid TTS: Browser Speech Synthesis (English) + Backend gTTS (Sinhala/Tamil)
  - Real-time chat interface with message history
  - Responsive design with animated UI elements
  - TypeScript for type safety and better developer experience

---

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+ & npm** (for frontend)
- **MongoDB** (for chat history storage)
  - MongoDB Atlas account or local MongoDB server
  - Connection string for database access

---

## ✨ Features

### 🎤 Advanced Voice Processing
- **ElevenLabs Speech-to-Text**: High-accuracy transcription using `scribe_v1` model
- **Hybrid TTS Architecture**:
  - Browser Web Speech Synthesis API for English (instant, offline)
  - Backend gTTS service for Sinhala/Tamil (accurate pronunciation)
  - Automatic fallback system for unsupported languages
- **Configurable Speed**: 1.3x default playback rate for faster responses
- **Client-side Processing**: 60-70% faster than server-side audio transfer
- **Real-time Feedback**: Visual indicators for recording and playback status

### 🤖 Intelligent AI Integration
- **LangGraph Routing**: Automatically routes queries to optimal AI model
- **Multi-model Support**:
  - OpenAI GPT-4 for English and Tamil responses
  - Google Gemini for Sinhala language understanding
- **Context-aware Responses**: Memory retention across conversations
- **Structured Outputs**: Step-by-step guidance for emergency procedures

### 🌍 Multilingual Support
- **Three Languages**: English, Sinhala (සිංහල), Tamil (தமிழ்)
- **Auto-detection**: Automatically identifies user's language
- **Language-specific Models**: Optimized AI for each language
- **Unicode Support**: Full support for Sinhala and Tamil scripts

### 💾 Data Persistence
- **MongoDB Integration**: Stores all chat history with timestamps
- **Conversation Context**: Maintains context across sessions
- **Message Metadata**: Tracks language, type, and response format
- **Scalable Storage**: Cloud-ready with MongoDB Atlas support

### 🚨 Emergency Features
- **Quick Action Buttons**: One-click access to common emergencies
  - 🔥 Fire emergency procedures
  - 🚪 Break-in safety protocols
  - 🏥 Medical emergency guidance
  - 👮 Police assistance coordination
- **Step-by-step Guidance**: Clear, actionable instructions
- **Priority Response**: Optimized for time-critical situations

### 🎨 User Experience
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Theme**: Automatic theme switching support
- **Animated UI**: Smooth transitions and visual feedback
- **Accessibility**: Keyboard navigation and screen reader support
- **Error Handling**: Graceful degradation with helpful error messages

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
   ```sh
   pip install -r requirements.txt
   ```
   
   **Key Dependencies:**
   - `fastapi==0.109.0` - Modern web framework
   - `uvicorn==0.27.0` - ASGI server
   - `langchain==0.1.0` - LLM orchestration
   - `langgraph==0.0.15` - Intelligent routing
   - `langchain-openai==0.0.2` - OpenAI integration
   - `langchain-google-genai==2.0.0` - Google Gemini integration
   - `pymongo==4.6.0` - MongoDB driver
   - `gTTS==2.4.0` - Text-to-speech for Sinhala/Tamil
   - `python-dotenv==1.0.0` - Environment management

4. **Environment Variables:**
   - Create a `.env` file in `AI_backend/` with the following variables:
     ```env
     # OpenAI Configuration (for English/Tamil)
     OPENAI_API_KEY=your_openai_api_key_here
     
     # Google Gemini Configuration (for Sinhala)
     GOOGLE_API_KEY=your_google_api_key_here
     
     # Server Configuration
     PORT=8000
     HOST=0.0.0.0
     
     # Model Configuration
     OPENAI_MODEL=gpt-4-turbo-preview
     GEMINI_MODEL=gemini-1.5-flash
     
     # Logging Configuration
     LOG_LEVEL=INFO
     
     # MongoDB Configuration
     MONGODB_URI=your_mongodb_connection_string
     MONGO_DB_NAME=User_History
     MONGO_COLLECTION=chat_history
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
   
   **Key Dependencies:**
   - `react` & `react-dom` - UI framework
   - `typescript` - Type safety
   - `@elevenlabs/client` - Speech-to-text integration
   - Standard React tooling (react-scripts, testing libraries)

3. **Environment Variables:**
   - Create a `.env` file in `Frontend/` with:
     ```env
     # ElevenLabs API (for speech-to-text)
     REACT_APP_ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
     
     # Backend API URL
     REACT_APP_API_URL=http://localhost:8000
     
     # TTS Configuration
     REACT_APP_TTS_SPEED=1.3
     ```

4. **Start the development server:**
   ```sh
   npm start
   ```
   The frontend will be available at `http://localhost:3000`.

5. **Build for production:**
   ```sh
   npm run build
   ```
   This creates an optimized production build in the `build/` folder.

---

## 🚀 Usage

### Starting the Application

1. **Start Backend Server:**
   ```sh
   cd AI_backend
   python main.py
   ```
   Backend runs at `http://localhost:8000`

2. **Start Frontend Server:**
   ```sh
   cd Frontend
   npm start
   ```
   Frontend runs at `http://localhost:3000`

### Using the Chat Interface

**Text Chat:**
1. Type your message in the input box
2. Press Enter or click Send
3. Receive AI-generated response in your language

**Voice Chat:**
1. Click the microphone button to start recording
2. Speak your emergency situation in Sinhala, English, or Tamil
3. Click stop when finished
4. Your speech is transcribed by ElevenLabs
5. AI responds in text
6. Response is spoken back using appropriate TTS:
   - English: Browser voice (instant)
   - Sinhala/Tamil: Backend gTTS (high quality)

**Quick Actions:**
- Click any emergency button for immediate guidance
- Responses are context-aware and actionable

### API Endpoints

**POST `/chat`**
- **Input**: `{ "message": "your text message" }`
- **Output**: `{ "response": { "type": "text|steps", "content": "..." }, "language": "en|si|ta" }`
- **Purpose**: Text-based chat processing with language detection

**POST `/tts`**
- **Input**: `{ "text": "text to speak", "language": "en|si|ta" }`
- **Output**: Audio stream (MP3)
- **Purpose**: Generate speech for Sinhala/Tamil text
- **Features**: Optimized for speed, 1-hour cache, 500-char limit

---

## 📋 Technical Notes

### API Keys Required
- **OpenAI API Key**: For English and Tamil responses (GPT-4)
  - Get it from: https://platform.openai.com/api-keys
- **Google Gemini API Key**: For Sinhala responses
  - Get it from: https://makersuite.google.com/app/apikey
- **ElevenLabs API Key**: For speech-to-text transcription
  - Get it from: https://elevenlabs.io/app/settings/api-keys

### Voice Processing Architecture

**Speech-to-Text (STT):**
- **Provider**: ElevenLabs Conversational AI
- **Model**: `scribe_v1`
- **Location**: Client-side (Frontend)
- **Languages**: Supports Sinhala, English, Tamil
- **Performance**: ~2-3 seconds for 10-second audio

**Text-to-Speech (TTS):**
- **English**: Browser Web Speech Synthesis API (instant, offline)
- **Sinhala/Tamil**: Backend gTTS service (1-3 seconds, high quality)
- **Fallback**: Automatic switching if browser voice unavailable
- **Speed**: Configurable via `REACT_APP_TTS_SPEED` (default: 1.3x)

**Performance Optimization:**
- ✅ Client-side processing eliminates audio file uploads/downloads
- ✅ 60-70% faster than server-side architecture
- ✅ Reduces backend load and bandwidth usage
- ✅ Caching for frequently used phrases (1-hour TTL)
- ✅ Text truncation for faster gTTS generation (500 char limit)

### Database Integration
- **MongoDB** for persistent chat history
- **Collections**: `chat_history` (single collection for all messages)
- **Schema**: 
  ```javascript
  {
    user_id: String,
    message: String,
    response: String,
    timestamp: Date,
    language: String,
    type: String  // "text" or "steps"
  }
  ```
- **Indexing**: Timestamp-based for efficient querying
- **Cloud Ready**: Works with MongoDB Atlas

### AI Model Routing
- **LangGraph**: Intelligent routing based on language detection
- **English & Tamil**: OpenAI GPT-4-turbo-preview
  - Reasoning: Superior multilingual understanding
  - Token limit: 128K context window
- **Sinhala**: Google Gemini 1.5 Flash
  - Reasoning: Better Sinhala language support
  - Native Unicode handling
- **Automatic Fallback**: If primary model fails, uses alternative

### Security Features
- **CORS Protection**: Configured for localhost development
- **Environment Variables**: Sensitive keys stored in .env files
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Graceful degradation with user-friendly messages
- **Rate Limiting**: Consider adding for production (e.g., slowapi)

### Browser Compatibility
- **Recommended**: Chrome/Edge (best Web Speech API support)
- **Firefox**: Limited voice selection
- **Safari**: iOS requires user interaction for audio playback
- **Mobile**: Full support with MediaRecorder API

### Development Tips
- Use `--reload` flag with uvicorn during development
- Enable React DevTools for frontend debugging
- Check browser console for speech service logs
- Monitor backend logs for API errors
- Test with different languages to verify routing

### Production Deployment
- **Backend**: 
  - Use `uvicorn main:app --host 0.0.0.0 --port 8000` (remove --reload)
  - Consider gunicorn with uvicorn workers
  - Set up reverse proxy (nginx/Apache)
  - Enable HTTPS with SSL certificates
- **Frontend**:
  - Run `npm run build` for optimized production build
  - Serve static files via CDN or web server
  - Update `REACT_APP_API_URL` to production backend URL
- **Database**:
  - Use MongoDB Atlas or managed MongoDB service
  - Set up proper authentication and IP whitelisting
  - Configure connection pooling
- **Environment**:
  - Never commit `.env` files to version control
  - Use secrets management (AWS Secrets, Azure Key Vault)
  - Set up monitoring and logging (Sentry, DataDog)

---

## 🔧 Troubleshooting

### Common Issues

**Backend Won't Start:**
- ✓ Check Python version: `python --version` (need 3.8+)
- ✓ Verify all dependencies installed: `pip install -r requirements.txt`
- ✓ Confirm `.env` file exists in `AI_backend/` directory
- ✓ Check if port 8000 is already in use
- ✓ Verify API keys are valid and not expired

**Frontend Won't Start:**
- ✓ Check Node.js version: `node --version` (need 16+)
- ✓ Delete `node_modules/` and reinstall: `npm install`
- ✓ Clear npm cache: `npm cache clean --force`
- ✓ Check if port 3000 is already in use
- ✓ Verify `.env` file exists in `Frontend/` directory

**CORS Errors:**
- ✓ Ensure backend is running at `http://localhost:8000`
- ✓ Check `REACT_APP_API_URL` in frontend `.env`
- ✓ Verify CORS middleware is enabled in `main.py`
- ✓ Clear browser cache and reload

**MongoDB Connection Issues:**
- ✓ Verify `MONGODB_URI` format: `mongodb+srv://user:pass@cluster.mongodb.net/dbname`
- ✓ Check IP whitelist in MongoDB Atlas (add 0.0.0.0/0 for testing)
- ✓ Confirm MongoDB service is running (if local)
- ✓ Test connection: `python test_mongo_connection.py`
- ✓ Check network firewall settings

**Voice Chat Not Working:**
- ✓ Grant microphone permissions in browser
- ✓ Check `REACT_APP_ELEVENLABS_API_KEY` is set correctly
- ✓ Verify ElevenLabs API quota hasn't been exceeded
- ✓ Test with Chrome/Edge (best compatibility)
- ✓ Check browser console for error messages
- ✓ Ensure HTTPS or localhost (required for MediaRecorder)

**TTS Silent or English Voice for Sinhala:**
- ✓ Check backend logs for `/tts` endpoint errors
- ✓ Verify `gTTS` is installed: `pip show gTTS`
- ✓ Check browser console for "Using backend TTS" message
- ✓ Ensure backend server is running
- ✓ Test TTS endpoint directly: `curl -X POST http://localhost:8000/tts -H "Content-Type: application/json" -d '{"text":"හෙලෝ","language":"si"}'`

**Sinhala/Tamil Not Displaying:**
- ✓ Ensure browser has Sinhala/Tamil fonts installed
- ✓ Check HTML charset is UTF-8
- ✓ Verify MongoDB stores Unicode correctly
- ✓ Test with different browsers

**Slow Response Times:**
- ✓ Check internet connection (AI APIs require network)
- ✓ Monitor API rate limits (OpenAI, Gemini, ElevenLabs)
- ✓ Verify MongoDB connection latency
- ✓ Check backend server resources (CPU, memory)
- ✓ Consider using faster AI models (e.g., gpt-3.5-turbo)

**AI Responses in Wrong Language:**
- ✓ Language detection happens automatically
- ✓ Check if text contains mixed languages (confuses detection)
- ✓ Verify `OPENAI_API_KEY` and `GOOGLE_API_KEY` are both set
- ✓ Check backend logs for routing decisions
- ✓ Test with pure single-language input

### Debug Mode

**Enable Verbose Logging:**

Backend (`main.py`):
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Frontend: Open browser DevTools (F12) and check:
- Console tab: Speech service logs
- Network tab: API request/response
- Application tab: Environment variables

### Getting Help

- Check browser console for error messages
- Check backend terminal for Python traceback
- Review `requirements.txt` for version conflicts
- Test each component independently
- Verify environment variables are loaded: `console.log(process.env)` (frontend), `print(os.getenv('KEY'))` (backend)

---

## 📊 Performance Metrics

- **Text Chat Response**: ~1-3 seconds (depends on AI model)
- **Voice Transcription (ElevenLabs)**: ~2-3 seconds for 10-second audio
- **English TTS (Browser)**: Instant (<100ms)
- **Sinhala/Tamil TTS (gTTS)**: ~1-3 seconds
- **Overall Voice Chat**: ~5-8 seconds end-to-end (60-70% faster than server-side)
- **Memory Usage (Backend)**: ~150-300 MB
- **Memory Usage (Frontend)**: ~50-100 MB

## 🔄 Version History

### v2.0.0 (Current) - Speech Optimization Update
- ✅ Migrated STT to ElevenLabs (from OpenAI Whisper)
- ✅ Implemented hybrid TTS architecture
- ✅ Moved speech processing to frontend (60-70% faster)
- ✅ Added configurable TTS speed control
- ✅ Optimized gTTS endpoint with caching
- ✅ Removed `/voice_chat` endpoint (deprecated)
- ✅ Enhanced error handling and logging

### v1.0.0 - Initial Release
- Basic text chat with OpenAI GPT-3.5-turbo
- Server-side voice processing
- MongoDB integration
- Multi-language support

## 🤝 Contributing

This project is for educational and emergency assistance purposes. Contributions are welcome!

**How to Contribute:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Commit changes: `git commit -m 'Add YourFeature'`
4. Push to branch: `git push origin feature/YourFeature`
5. Open a Pull Request

**Contribution Guidelines:**
- Follow existing code style (PEP 8 for Python, ESLint for TypeScript)
- Add comments for complex logic
- Update README for new features
- Test thoroughly before submitting
- Include screenshots for UI changes

## 📜 License

This project is for educational and emergency assistance purposes only.

**Disclaimer:** This is an AI-powered assistant and should not replace professional emergency services. Always call local emergency numbers (119 in Sri Lanka) for immediate assistance.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **Google** for Gemini API
- **ElevenLabs** for Conversational AI
- **MongoDB** for database solutions
- **FastAPI** and **React** communities for excellent frameworks

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the Troubleshooting section above
- Review browser console and backend logs

---

**Built with ❤️ for Sri Lanka's emergency response needs** 