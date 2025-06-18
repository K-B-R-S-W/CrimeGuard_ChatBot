import React, { useState, useEffect, useRef, ChangeEvent, KeyboardEvent, FC } from 'react';
import './Css/App.css';

interface Message {
  content: string | React.ReactNode;
  type: 'user' | 'bot';
  isTyping?: boolean;
  isAudio?: boolean;
}

const translations = {
  en: {
    welcome: "Welcome to Sri Lanka Emergency Assistant. In an emergency, please don't hesitate - call 119 for Police, 110 for Fire & Rescue, or 1990 for Ambulance (Suwa Seriya). I can provide guidance for different emergency situations in Sri Lanka.",
    priority: "ALWAYS call emergency services first before taking any advice.",
    placeholder: "Describe your emergency situation...",
    sendBtn: "Send",
    voiceBtn: "Voice",
    contactsTitle: "Sri Lanka Emergency Contacts:",
    fire: "Fire",
    breakIn: "Break-in",
    medical: "Medical",
    police: "Police"
  },
  si: {
    welcome: "ශ්‍රී ලංකා හදිසි ආධාර සහායකයා වෙත සාදරයෙන් පිළිගනිමු. හදිසි අවස්ථාවකදී, පොලිසිය සඳහා 119, ගිනි නිවීමේ හා ගලවා ගැනීමේ සේවාව සඳහා 110, හෝ ගිලන් රථ සේවාව (සුව සැරිය) සඳහා 1990 අමතන්න. මට ශ්‍රී ලංකාවේ විවිධ හදිසි අවස්ථා සඳහා මග පෙන්වීමක් ලබා දිය හැකිය.",
    priority: "හදිසි අවස්ථාවක දී සැමවිටම උපදෙස් ලබා ගැනීමට පෙර හදිසි සේවා ඇමතීම අවශ්‍ය වේ.",
    placeholder: "ඔබේ හදිසි තත්වය විස්තර කරන්න...",
    sendBtn: "යවන්න",
    voiceBtn: "හඬ",
    contactsTitle: "ශ්‍රී ලංකා හදිසි සම්බන්ධතා:",
    fire: "ගින්න",
    breakIn: "බිඳීම",
    medical: "වෛද්‍ය",
    police: "පොලිසිය"
  },
  ta: {
    welcome: "இலங்கை அவசர உதவியாளருக்கு வரவேற்கிறோம். அவசரநிலையில், தயவுசெய்து தயங்காதீர்கள் - காவல்துறைக்கு 119, தீயணைப்பு & மீட்புக்கு 110, அல்லது ஆம்புலன்ஸுக்கு (சுவ செரிய) 1990ஐ அழைக்கவும். இலங்கையில் பல்வேறு அவசரநிலைகளுக்கு நான் வழிகாட்டலை வழங்க முடியும்.",
    priority: "எப்போதும் அறிவுரை பெறுவதற்கு முன் அவசர சேவைகளை அழைக்கவும்.",
    placeholder: "உங்கள் அவசரநிலையை விவரிக்கவும்...",
    sendBtn: "அனுப்பு",
    voiceBtn: "குரல்",
    contactsTitle: "இலங்கை அவசர தொடர்புகள்:",
    fire: "தீ",
    breakIn: "உடைப்பு",
    medical: "மருத்துவம்",
    police: "காவல்துறை"
  }
};

const App: FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { content: "Welcome to Sri Lanka Emergency Assistant. In an emergency, please don't hesitate - call 119 for Police, 110 for Fire & Rescue, or 1990 for Ambulance (Suwa Seriya). I can provide guidance for different emergency situations in Sri Lanka.", type: 'bot' },
    { content: "ALWAYS call emergency services first before taking any advice.", type: 'bot' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkTheme(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    createParticles();
  }, []);

  const createParticles = () => {
    const background = document.querySelector('.emergency-background');
    if (!background) return;

    for (let i = 0; i < 30; i++) {
      const particle = document.createElement('div');
      particle.classList.add('particle');
      const size = Math.random() * 8 + 2;
      const posX = Math.random() * 100;
      const posY = Math.random() * 100;
      const opacity = Math.random() * 0.3 + 0.1;
      const duration = Math.random() * 20 + 10;
      const delay = Math.random() * 10;
      
      Object.assign(particle.style, {
        width: `${size}px`,
        height: `${size}px`,
        left: `${posX}%`,
        top: `${posY}%`,
        opacity: opacity.toString(),
        background: `rgba(255, 255, 255, ${opacity})`,
        animation: `float ${duration}s infinite ease-in-out`,
        animationDelay: `${delay}s`
      });
      
      background.appendChild(particle);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleTheme = () => {
    setIsDarkTheme(prev => {
      const newTheme = !prev;
      document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
      localStorage.setItem('theme', newTheme ? 'dark' : 'light');
      return newTheme;
    });
  };

  const addMessage = (content: string | React.ReactNode, type: 'user' | 'bot', isTyping: boolean = false, isAudio?: boolean) => {
    setMessages(prev => [...prev, { content, type, isTyping, isAudio }]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    addMessage(inputMessage, 'user');
    setInputMessage('');
    addMessage('Assistant is analyzing your situation...', 'bot', true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputMessage })
      });

      const data = await response.json();
      
      // Remove typing message
      setMessages(prev => prev.filter(msg => !msg.isTyping));

      if (data.response.type === 'steps') {
        addMessage(
          <ul>
            {data.response.content.map((step: string, idx: number) => (
              <li key={idx}>{step}</li>
            ))}
          </ul>,
          'bot'
        );
      } else {
        addMessage(data.response.content, 'bot');
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      addMessage("I apologize, but I'm experiencing technical difficulties. If this is an emergency, please call emergency services immediately (119 for Police, 110 for Fire, 1990 for Ambulance).", 'bot');
    }
  };

  const toggleRecording = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/mp3' });
          await sendVoiceMessage(audioBlob);
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        addMessage('Unable to access microphone. Please check permissions.', 'bot');
      }
    } else {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.mp3');

    addMessage('Assistant is processing your voice message...', 'bot', true);

    try {
      const response = await fetch('http://localhost:8000/voice_chat', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Voice processing failed');

      const data = await response.json();
      setMessages(prev => prev.filter(msg => !msg.isTyping));

      // Add the text response as a chat message
      addMessage(data.text_response, 'bot');

      // Use browser TTS to speak the response
      if (data.text_response) {
        const utterance = new window.SpeechSynthesisUtterance(data.text_response);
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      addMessage('I apologize, but there was an issue processing your voice message. If this is an emergency, please call emergency services immediately (119 for Police, 110 for Fire, 1990 for Ambulance).', 'bot');
    }
  };

  const quickQuestion = (question: string) => {
    setInputMessage(question);
    sendMessage();
  };

  const handleLanguageChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value;
    setCurrentLanguage(lang);
    setMessages(prev => {
      const updated = [...prev];
      // Update the first two bot messages if they exist
      if (updated[0] && updated[0].type === 'bot') {
        updated[0] = { ...updated[0], content: translations[lang].welcome };
      }
      if (updated[1] && updated[1].type === 'bot') {
        updated[1] = { ...updated[1], content: translations[lang].priority };
      }
      return updated;
    });
  };

  const handleInputKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <>
      {/* Intro Section */}
      <div className="intro-section">
        <h1>CrimeGuard Emergency Assistant</h1>
        <p>Get immediate help in emergencies with our AI-powered assistant. We provide quick access to emergency services and vital information.</p>
        <div className="features-row">
          <div className="feature-card">
            <i className="fas fa-phone-volume"></i>
            <h3>Quick Contacts</h3>
            <p>Instantly connect with police, ambulance, fire brigade, and hospitals.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-map-marker-alt"></i>
            <h3>Location Services</h3>
            <p>Share your precise location to get help to you faster.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-language"></i>
            <h3>Multi-Language Support</h3>
            <p>Communicate in Sinhala, Tamil, or English.</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-microphone"></i>
            <h3>Voice Commands</h3>
            <p>Use voice to send messages and report emergencies.</p>
          </div>
        </div>
      </div>

      {/* Chatbot Section (conditionally rendered below the intro) */}
      {isChatOpen && (
        <div className="chat-container open">
          <div className="chat-header">
            <i className="fas fa-shield-alt"></i>
            Sri Lanka Emergency Assistant
            <select
              className="language-dropdown"
              value={currentLanguage}
              onChange={handleLanguageChange}
            >
              <option value="en">English</option>
              <option value="si">Sinhala</option>
              <option value="ta">Tamil</option>
            </select>
            <button className="theme-toggle" onClick={toggleTheme}>
              <i className={`fas fa-${isDarkTheme ? 'sun' : 'moon'}`}></i>
            </button>
          </div>
          <div className="emergency-buttons">
            <button
              className="emergency-button fire-button"
              onClick={() => quickQuestion(translations[currentLanguage].fire)}
            >
              <i className="fas fa-fire"></i> {translations[currentLanguage].fire}
            </button>
            <button
              className="emergency-button break-in-button"
              onClick={() => quickQuestion(translations[currentLanguage].breakIn)}
            >
              <i className="fas fa-door-open"></i> {translations[currentLanguage].breakIn}
            </button>
            <button
              className="emergency-button medical-button"
              onClick={() => quickQuestion(translations[currentLanguage].medical)}
            >
              <i className="fas fa-heartbeat"></i> {translations[currentLanguage].medical}
            </button>
            <button
              className="emergency-button police-button"
              onClick={() => quickQuestion(translations[currentLanguage].police)}
            >
              <i className="fas fa-user-shield"></i> {translations[currentLanguage].police}
            </button>
          </div>
          <div className="chat-messages" id="messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.type}-message ${message.isTyping ? 'typing' : ''} ${message.isAudio ? 'audio-message' : ''}`}>
                {typeof message.content === 'string' ? message.content : message.content}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={inputMessage}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputMessage(e.target.value)}
              onKeyPress={handleInputKeyPress}
              placeholder={translations[currentLanguage].placeholder}
            />
            <button className="send-button" onClick={sendMessage}>
              {translations[currentLanguage].sendBtn} <i className="fas fa-paper-plane"></i>
            </button>
            <button
              className={`voice-button ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
            >
              <i className={`fas fa-${isRecording ? 'stop' : 'microphone'}`}></i>
              {translations[currentLanguage].voiceBtn}
            </button>
          </div>
          <div className="emergency-contacts">
            <div className="contacts-title">{translations[currentLanguage].contactsTitle}</div>
            <div className="contacts-grid">
              <div className="contact-item">
                <i className="fas fa-ambulance"></i> Ambulance (Suwa Seriya): 1990
              </div>
              <div className="contact-item">
                <i className="fas fa-fire-extinguisher"></i> Fire & Rescue: 110
              </div>
              <div className="contact-item">
                <i className="fas fa-user-shield"></i> Police Emergency: 119
              </div>
              <div className="contact-item">
                <i className="fas fa-hospital"></i> Accident Service: 011-2691111
              </div>
              <div className="contact-item">
                <i className="fas fa-phone"></i> Disaster Management: 117
              </div>
              <div className="contact-item">
                <i className="fas fa-tint"></i> COVID-19 Hotline: 1390
              </div>
            </div>
          </div>
          <div className="disclaimer priority-message" style={{ textAlign: 'center', margin: '10px 0', fontWeight: 'bold', color: '#ff0000' }}>
            {translations[currentLanguage].priority}
          </div>
        </div>
      )}

      {/* Chat Toggle Icon (always visible, floating) */}
      <div
        className="chat-toggle-icon"
        onClick={() => setIsChatOpen(!isChatOpen)}
      >
        <i className={`fas fa-${isChatOpen ? 'times' : 'comment-dots'}`}></i>
      </div>

      {/* Animated Background (should be behind everything) */}
      <div className="emergency-background">
        <div className="ripple-container">
          {[0, 2, 4].map((delay) => (
            <div
              key={delay}
              className="ripple"
              style={{
                top: '50%',
                left: '50%',
                width: '300px',
                height: '300px',
                animationDelay: `${delay}s`
              }}
            />
          ))}
        </div>
        {/* Shields */}
        {[
          { top: '30%', left: '20%' },
          { top: '60%', left: '70%' },
          { top: '40%', left: '60%' }
        ].map((pos, index) => (
          <div key={index} className="shield" style={pos} />
        ))}
        {/* Security Icons */}
        {[
          { icon: 'lock', top: '20%', left: '15%', delay: '0s' },
          { icon: 'shield-alt', top: '70%', left: '20%', delay: '1s' },
          { icon: 'video', top: '30%', left: '80%', delay: '2s' },
          { icon: 'house-user', top: '75%', left: '75%', delay: '3s' },
          { icon: 'first-aid', top: '15%', left: '60%', delay: '4s' }
        ].map((item, index) => (
          <i
            key={index}
            className={`security-icon fas fa-${item.icon}`}
            style={{
              top: item.top,
              left: item.left,
              animationDelay: item.delay
            }}
          />
        ))}
        {/* Sri Lanka Flags */}
        <div className="sri-lanka-flag" style={{ top: '25%', left: '40%', animationDelay: '0s' }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600">
            <rect width="1200" height="600" fill="#FFBE00"/>
            <rect width="300" height="600" fill="#8D153A"/>
            <rect x="300" width="300" height="600" fill="#046A38"/>
            <rect x="600" width="600" height="600" fill="#FF883E"/>
          </svg>
        </div>
        <div className="sri-lanka-flag" style={{ top: '65%', left: '25%', animationDelay: '2s' }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600">
            <rect width="1200" height="600" fill="#FFBE00"/>
            <rect width="300" height="600" fill="#8D153A"/>
            <rect x="300" width="300" height="600" fill="#046A38"/>
            <rect x="600" width="600" height="600" fill="#FF883E"/>
          </svg>
        </div>
      </div>
    </>
  );
};

export default App; 