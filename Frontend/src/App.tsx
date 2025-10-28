import React, { useState, useEffect, useRef, ChangeEvent, KeyboardEvent, FC } from 'react';
import './Css/App.css';
import { transcribeAudio, speakText, stopSpeaking } from './utils/speechService';

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
    police: "Police",
    fireGuidance: "What should I do if there's a fire?",
    breakInGuidance: "What should I do if someone is breaking into my house?",
    medicalGuidance: "What should I do in a medical emergency?",
    policeGuidance: "When should I contact the police?"
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
    police: "පොලිසිය",
    fireGuidance: "ගින්නක් ඇති වුවහොත් මම කුමක් කළ යුතුද?",
    breakInGuidance: "කවුරුහරි මගේ නිවසට කඩා වැදීමට උත්සාහ කරන්නේ නම් මම කුමක් කළ යුතුද?",
    medicalGuidance: "වෛද්‍ය හදිසි අවස්ථාවකදී මම කුමක් කළ යුතුද?",
    policeGuidance: "මම පොලිසියට කවදා සම්බන්ධ විය යුතුද?"
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
    police: "காவல்துறை",
    fireGuidance: "தீ விபத்து ஏற்பட்டால் நான் என்ன செய்ய வேண்டும்?",
    breakInGuidance: "யாரோ என் வீட்டிற்குள் புகுந்தால் நான் என்ன செய்ய வேண்டும்?",
    medicalGuidance: "மருத்துவ அவசரநிலையில் நான் என்ன செய்ய வேண்டும்?",
    policeGuidance: "நான் எப்போது காவல்துறையை தொடர்பு கொள்ள வேண்டும்?"
  }
};

const App: FC = () => {
  // Generate unique session ID for this user (persistent across page refreshes)
  const [sessionId] = useState(() => {
    const stored = localStorage.getItem('chat_session_id');
    if (stored) return stored;
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chat_session_id', newId);
    return newId;
  });

  const [messages, setMessages] = useState<Message[]>([
    { content: "Welcome to Sri Lanka Emergency Assistant. In an emergency, please don't hesitate - call 119 for Police, 110 for Fire & Rescue, or 1990 for Ambulance (Suwa Seriya). I can provide guidance for different emergency situations in Sri Lanka.", type: 'bot' },
    { content: "ALWAYS call emergency services first before taking any advice.", type: 'bot' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Conversation history for context (client-side tracking)
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string, content: string}>>([]);

  // Emergency call tracker state (single call)
  const [showCallTracker, setShowCallTracker] = useState(false);
  const [currentCall, setCurrentCall] = useState<{
    sid: string;
    service: string;
    number: string;
    type: string;
    language: string;
  } | null>(null);
  const [callDuration, setCallDuration] = useState(0);
  const callTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Multi-emergency call tracker state (2+ calls)
  const [showMultiCallTracker, setShowMultiCallTracker] = useState(false);
  const [activeCalls, setActiveCalls] = useState<Array<{
    type: string;
    call_sid: string;
    status: string;
    priority?: number;
    duration: number;
  }>>([]);
  const multiCallTimersRef = useRef<{[key: string]: NodeJS.Timeout}>({});

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkTheme(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    createParticles();
    
    // Cleanup speech synthesis on unmount
    return () => {
      stopSpeaking();
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
      }
    };
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

  const cancelEmergencyCall = async () => {
    if (!currentCall) return;

    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/cancel_call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_sid: currentCall.sid })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('Call canceled successfully');
        addMessage(`Call to ${currentCall.service} has been canceled.`, 'bot');
      } else {
        console.error('Failed to cancel call:', data.error);
        addMessage(`Unable to cancel call: ${data.error}`, 'bot');
      }
    } catch (error) {
      console.error('Error canceling call:', error);
      addMessage('Error canceling the call. Please hang up manually if needed.', 'bot');
    } finally {
      // Close the tracker
      setShowCallTracker(false);
      setCurrentCall(null);
      setCallDuration(0);
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
      }
    }
  };

  // Cancel individual call in multi-emergency
  const cancelMultiEmergencyCall = async (callSid: string, callType: string) => {
    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/cancel_call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_sid: callSid })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log(`Call ${callSid} canceled successfully`);
        addMessage(`${callType.toUpperCase()} call has been canceled.`, 'bot');
        
        // Remove from active calls
        setActiveCalls(prev => prev.filter(call => call.call_sid !== callSid));
        
        // Clear timer for this call
        if (multiCallTimersRef.current[callSid]) {
          clearInterval(multiCallTimersRef.current[callSid]);
          delete multiCallTimersRef.current[callSid];
        }
        
        // If no more active calls, close the multi-tracker
        setActiveCalls(prev => {
          if (prev.length <= 1) {
            setShowMultiCallTracker(false);
            // Clear all remaining timers
            Object.values(multiCallTimersRef.current).forEach(timer => clearInterval(timer));
            multiCallTimersRef.current = {};
          }
          return prev.filter(call => call.call_sid !== callSid);
        });
        
      } else {
        console.error('Failed to cancel call:', data.error);
        addMessage(`Unable to cancel ${callType} call: ${data.error}`, 'bot');
      }
    } catch (error) {
      console.error('Error canceling call:', error);
      addMessage(`Error canceling ${callType} call.`, 'bot');
    }
  };

  // Cancel all emergency calls at once
  const cancelAllEmergencyCalls = async () => {
    if (activeCalls.length === 0) return;

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const cancelPromises = activeCalls.map(async (call) => {
      try {
        const response = await fetch(`${API_URL}/cancel_call`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ call_sid: call.call_sid })
        });

        const data = await response.json();
        
        if (data.success) {
          console.log(`Call ${call.call_sid} (${call.type}) canceled successfully`);
          return { success: true, type: call.type, sid: call.call_sid };
        } else {
          console.error(`Failed to cancel ${call.type} call:`, data.error);
          return { success: false, type: call.type, error: data.error };
        }
      } catch (error) {
        console.error(`Error canceling ${call.type} call:`, error);
        return { success: false, type: call.type, error: 'Network error' };
      }
    });

    const results = await Promise.all(cancelPromises);
    
    // Count successes and failures
    const successCount = results.filter(r => r.success).length;
    const failureCount = results.filter(r => !r.success).length;
    
    if (successCount > 0) {
      addMessage(`${successCount} emergency call(s) have been canceled successfully.`, 'bot');
    }
    if (failureCount > 0) {
      addMessage(`Failed to cancel ${failureCount} call(s). Please hang up manually if needed.`, 'bot');
    }

    // Close the multi-tracker and clear all timers
    setShowMultiCallTracker(false);
    Object.values(multiCallTimersRef.current).forEach(timer => clearInterval(timer));
    multiCallTimersRef.current = {};
    setActiveCalls([]);
  };

  // Close multi-call tracker manually
  const closeMultiCallTracker = () => {
    setShowMultiCallTracker(false);
    // Clear all timers
    Object.values(multiCallTimersRef.current).forEach(timer => clearInterval(timer));
    multiCallTimersRef.current = {};
    setActiveCalls([]);
  };

  const toggleTheme = () => {
    setIsDarkTheme(prev => {
      const newTheme = !prev;
      document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
      localStorage.setItem('theme', newTheme ? 'dark' : 'light');
      return newTheme;
    });
  };

  const detectLanguage = (text: string): string => {
    // Check for Sinhala characters (Unicode range: 0D80-0DFF)
    const sinhalaChars = (text.match(/[\u0D80-\u0DFF]/g) || []).length;
    // Check for Tamil characters (Unicode range: 0B80-0BFF)
    const tamilChars = (text.match(/[\u0B80-\u0BFF]/g) || []).length;
    // Check for English/Latin characters
    const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
    
    const totalChars = sinhalaChars + tamilChars + englishChars;
    
    if (totalChars === 0) return currentLanguage; // Default to current language if no alphabet characters
    
    // Determine the dominant language
    if (sinhalaChars > tamilChars && sinhalaChars > englishChars) {
      return 'si';
    } else if (tamilChars > sinhalaChars && tamilChars > englishChars) {
      return 'ta';
    } else {
      return 'en';
    }
  };

  const addMessage = (content: string | React.ReactNode, type: 'user' | 'bot', isTyping: boolean = false, isAudio?: boolean) => {
    setMessages(prev => [...prev, { content, type, isTyping, isAudio }]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage;
    addMessage(userMessage, 'user');
    setInputMessage('');
    
    // Add to conversation history (client-side)
    const updatedHistory = [...conversationHistory, { role: 'user', content: userMessage }];
    setConversationHistory(updatedHistory);
    
    // Detect language from the user's message
    const detectedLanguage = detectLanguage(userMessage);
    
    addMessage('Assistant is analyzing your situation...', 'bot', true);

    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage,
          language: detectedLanguage,
          session_id: sessionId,  // Send unique session ID
          conversation_history: updatedHistory  // Send conversation context
        })
      });

      const data = await response.json();
      
      // Remove typing message
      setMessages(prev => prev.filter(msg => !msg.isTyping));

      // Check if this was an emergency call
      if (data.emergency_call) {
        // Display emergency response with special styling
        addMessage(data.response, 'bot');
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
        
        // CHECK: Multi-emergency or single emergency?
        if (data.multi_emergency && data.calls && data.calls.length > 1) {
          // MULTI-EMERGENCY: Show multi-call tracker
          console.log(`Multi-emergency detected: ${data.calls.length} calls`);
          
          const callsWithTimers = data.calls
            .filter((call: any) => call.status === 'initiated' && call.call_sid)
            .map((call: any) => ({
              type: call.type,
              call_sid: call.call_sid,
              status: call.status,
              priority: call.priority,
              duration: 0
            }));
          
          setActiveCalls(callsWithTimers);
          setShowMultiCallTracker(true);
          
          // Start individual timers for each call
          callsWithTimers.forEach((call: any) => {
            multiCallTimersRef.current[call.call_sid] = setInterval(() => {
              setActiveCalls(prev => 
                prev.map(c => 
                  c.call_sid === call.call_sid 
                    ? {...c, duration: c.duration + 1} 
                    : c
                )
              );
            }, 1000);
          });
          
        } else if (data.call_initiated && data.call_sid) {
          // SINGLE EMERGENCY: Show single call tracker
          console.log(`Emergency call initiated: ${data.emergency_type} - SID: ${data.call_sid}`);
          
          // Set current call data
          setCurrentCall({
            sid: data.call_sid,
            service: data.service_name,
            number: data.emergency_number,
            type: data.emergency_type,
            language: data.language
          });
          
          // Show call tracker
          setShowCallTracker(true);
          setCallDuration(0);
          
          // Start call duration timer
          if (callTimerRef.current) {
            clearInterval(callTimerRef.current);
          }
          callTimerRef.current = setInterval(() => {
            setCallDuration(prev => prev + 1);
          }, 1000);
        }
      } else {
        // Normal chat response
        let botResponseText = '';
        
        if (data.response.type === 'steps') {
          botResponseText = data.response.content.join('\n');
          addMessage(
            <ul>
              {data.response.content.map((step: string, idx: number) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>,
            'bot'
          );
        } else {
          botResponseText = data.response.content;
          addMessage(data.response.content, 'bot');
        }
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: botResponseText }]);
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      const errorMsg = "I apologize, but I'm experiencing technical difficulties. If this is an emergency, please call emergency services immediately (119 for Police, 110 for Fire, 1990 for Ambulance).";
      addMessage(errorMsg, 'bot');
      setConversationHistory(prev => [...prev, { role: 'assistant', content: errorMsg }]);
    }
  };

  const toggleRecording = async () => {
    // Cancel any ongoing speech synthesis
    window.speechSynthesis.cancel();

    if (!isRecording) {
      try {
        // Stop any existing stream
        if (mediaRecorderRef.current) {
          mediaRecorderRef.current.stop();
          const tracks = mediaRecorderRef.current.stream.getTracks();
          tracks.forEach(track => track.stop());
        }
        
        // Request high-quality audio
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: 44100,
          }
        });
        
        // Check supported MIME types
        let mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported('audio/webm')) {
          if (MediaRecorder.isTypeSupported('audio/ogg')) {
            mimeType = 'audio/ogg';
          } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
          } else {
            mimeType = 'audio/mp3';
          }
        }

        const mediaRecorder = new MediaRecorder(stream, {
          mimeType,
          audioBitsPerSecond: 128000
        });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          if (audioChunksRef.current.length === 0) {
            addMessage('No audio was recorded. Please try again.', 'bot');
            return;
          }
          // Create blob with the correct mime type
          const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });
          
          // Check if the blob is valid
          if (audioBlob.size < 1024) {
            addMessage('Recording was too short. Please speak for a longer duration.', 'bot');
            return;
          }
          
          await sendVoiceMessage(audioBlob);
          stream.getTracks().forEach(track => track.stop());
        };

        // Request data every second and start recording
        mediaRecorder.start(1000);
        setIsRecording(true);
        setRecordingTime(0);
        
        // Start the recording timer
        recordingTimerRef.current = setInterval(() => {
          setRecordingTime(prev => {
            if (prev >= 29) { // Stop at 30 seconds
              if (mediaRecorderRef.current?.state === 'recording') {
                mediaRecorderRef.current.stop();
                setIsRecording(false);
              }
              if (recordingTimerRef.current) {
                clearInterval(recordingTimerRef.current);
              }
            }
            return prev + 1;
          });
        }, 1000);
        
        // Add a timeout to automatically stop recording after 30 seconds
        setTimeout(() => {
          if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
          }
          if (recordingTimerRef.current) {
            clearInterval(recordingTimerRef.current);
          }
        }, 30000);
      } catch (error) {
        addMessage('Unable to access microphone. Please check permissions.', 'bot');
        setIsRecording(false);
      }
    } else {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob: Blob) => {
    try {
      // Step 1: Transcribe audio using ElevenLabs (client-side)
      addMessage('Transcribing your speech...', 'bot', true);
      
      const transcription = await transcribeAudio(audioBlob);
      
      if (!transcription || transcription.trim().length === 0) {
        setMessages(prev => prev.filter(msg => !msg.isTyping));
        addMessage('Could not understand the audio. Please speak clearly and try again.', 'bot');
        return;
      }

      // Remove transcription message and add the transcribed user message
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      addMessage(transcription, 'user');
      
      // Add to conversation history
      const updatedHistory = [...conversationHistory, { role: 'user', content: transcription }];
      setConversationHistory(updatedHistory);
      
      // Step 2: Send transcription to backend for AI response (text only)
      addMessage('Assistant is analyzing your message...', 'bot', true);
      
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: transcription,
          session_id: sessionId,  // Send unique session ID
          conversation_history: updatedHistory  // Send conversation context
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from server');
      }

      const data = await response.json();
      
      // Remove processing message
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      
      // Check if this was an emergency call
      if (data.emergency_call) {
        // Display emergency response
        addMessage(data.response, 'bot');
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
        
        // CHECK: Multi-emergency or single emergency?
        if (data.multi_emergency && data.calls && data.calls.length > 1) {
          // MULTI-EMERGENCY: Show multi-call tracker
          console.log(`Multi-emergency detected: ${data.calls.length} calls`);
          
          const callsWithTimers = data.calls
            .filter((call: any) => call.status === 'initiated' && call.call_sid)
            .map((call: any) => ({
              type: call.type,
              call_sid: call.call_sid,
              status: call.status,
              priority: call.priority,
              duration: 0
            }));
          
          setActiveCalls(callsWithTimers);
          setShowMultiCallTracker(true);
          
          // Start individual timers for each call
          callsWithTimers.forEach((call: any) => {
            multiCallTimersRef.current[call.call_sid] = setInterval(() => {
              setActiveCalls(prev => 
                prev.map(c => 
                  c.call_sid === call.call_sid 
                    ? {...c, duration: c.duration + 1} 
                    : c
                )
              );
            }, 1000);
          });
          
        } else if (data.call_initiated && data.call_sid) {
          // SINGLE EMERGENCY: Show single call tracker
          console.log(`Emergency call initiated: ${data.emergency_type} - SID: ${data.call_sid}`);
          
          // Set current call data
          setCurrentCall({
            sid: data.call_sid,
            service: data.service_name,
            number: data.emergency_number,
            type: data.emergency_type,
            language: data.language
          });
          
          // Show call tracker
          setShowCallTracker(true);
          setCallDuration(0);
          
          // Start call duration timer
          if (callTimerRef.current) {
            clearInterval(callTimerRef.current);
          }
          callTimerRef.current = setInterval(() => {
            setCallDuration(prev => prev + 1);
          }, 1000);
        }
        
        // For emergency calls, also speak the response
        const detectedLanguage = data.language || 'en';
        try {
          await speakText(data.response, detectedLanguage);
        } catch (err) {
          console.error('Error during emergency speech synthesis:', err);
        }
        return;
      }
      
      // Step 3: Display and speak the response (normal flow)
      if (data.response) {
        let responseText = '';
        let displayContent: string | React.ReactNode = '';
        
        // Handle formatted response (steps or text)
        if (typeof data.response === 'object') {
          if (data.response.type === 'steps' && Array.isArray(data.response.content)) {
            // Format as list for display
            displayContent = (
              <ul>
                {data.response.content.map((step: string, idx: number) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            );
            // For TTS, join all steps with periods
            responseText = data.response.content.join('. ');
          } else if (data.response.content) {
            responseText = data.response.content;
            displayContent = responseText;
          } else {
            responseText = JSON.stringify(data.response);
            displayContent = responseText;
          }
        } else {
          responseText = data.response;
          displayContent = responseText;
        }
        
        // Add the message to display
        addMessage(displayContent, 'bot');
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: responseText }]);
        
        // Step 4: Use browser TTS to speak the response (client-side)
        const detectedLanguage = data.language || 'en';
        console.log('About to speak:', responseText.substring(0, 50), 'in language:', detectedLanguage);
        
        try {
          await speakText(responseText, detectedLanguage);
          console.log('Speech completed successfully');
        } catch (err) {
          console.error('Error during speech synthesis:', err);
          // Speech failed but message is still displayed
        }
      }
    } catch (error) {
      console.error('Voice message error:', error);
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      const errorMsg = 'I apologize, but there was an issue processing your voice message. If this is an emergency, please call emergency services immediately (119 for Police, 110 for Fire, 1990 for Ambulance).';
      addMessage(errorMsg, 'bot');
      setConversationHistory(prev => [...prev, { role: 'assistant', content: errorMsg }]);
    }
  };

  const quickQuestion = async (question: string) => {
    // Add the question to messages immediately
    addMessage(question, 'user');
    
    // Add to conversation history (client-side)
    const updatedHistory = [...conversationHistory, { role: 'user', content: question }];
    setConversationHistory(updatedHistory);
    
    // Detect language from the question
    const detectedLanguage = detectLanguage(question);
    
    addMessage('Assistant is analyzing your situation...', 'bot', true);

    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: question,
          language: detectedLanguage,
          session_id: sessionId,  // Send unique session ID
          conversation_history: updatedHistory  // Send conversation context
        })
      });

      const data = await response.json();
      
      // Remove typing message
      setMessages(prev => prev.filter(msg => !msg.isTyping));

      // Check if this was an emergency call
      if (data.emergency_call) {
        // Display emergency response
        addMessage(data.response, 'bot');
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
        
        if (data.call_initiated) {
          console.log(`Emergency call initiated: ${data.emergency_type} - SID: ${data.call_sid}`);
        }
      } else {
        // Normal response
        let botResponseText = '';
        
        if (data.response.type === 'steps') {
          botResponseText = data.response.content.join('\n');
          addMessage(
            <ul>
              {data.response.content.map((step: string, idx: number) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>,
            'bot'
          );
        } else {
          botResponseText = data.response.content;
          addMessage(data.response.content, 'bot');
        }
        
        // Add bot response to conversation history
        setConversationHistory(prev => [...prev, { role: 'assistant', content: botResponseText }]);
      }
    } catch (error) {
      setMessages(prev => prev.filter(msg => !msg.isTyping));
      const errorMsg = "I apologize, but I'm experiencing technical difficulties. If this is an emergency, please call emergency services immediately (119 for Police, 110 for Fire, 1990 for Ambulance).";
      addMessage(errorMsg, 'bot');
      setConversationHistory(prev => [...prev, { role: 'assistant', content: errorMsg }]);
    }
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
      {/* Emergency Call Tracker Popup */}
      {showCallTracker && currentCall && (
        <div className="call-tracker-overlay">
          <div className="call-tracker-popup">
            <div className="call-tracker-header">
              <div className="call-tracker-icon">🚨</div>
            </div>
            
            <div className="call-tracker-content">
              <div className="call-tracker-service">{currentCall.service}</div>
              <div className="call-tracker-number">{currentCall.number}</div>
              
              <div className="call-tracker-animation">
                <div className="call-pulse">
                  <i className="fas fa-phone-alt"></i>
                </div>
              </div>
              
              <div className="call-tracker-status">Calling...</div>
              <div className="call-tracker-timer">
                {Math.floor(callDuration / 60)}:{(callDuration % 60).toString().padStart(2, '0')}
              </div>
              
              <div className="call-tracker-actions">
                <button className="cancel-call-btn" onClick={cancelEmergencyCall}>
                  <i className="fas fa-phone-slash"></i>
                  Cancel Call
                </button>
              </div>
              
              <div className="call-tracker-warning">
                ⚠️ This call is being placed to emergency services. Only cancel if this was a mistake.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Call Tracker for Multiple Emergencies */}
      {showMultiCallTracker && activeCalls.length > 0 && (
        <div className="call-tracker-overlay">
          <div className="multi-call-tracker-popup">
            <div className="multi-call-tracker-header">
              <h3><span className="call-tracker-icon">🚨</span> Active Emergency Calls ({activeCalls.length})</h3>
              <button className="close-tracker-btn" onClick={closeMultiCallTracker}>
                <i className="fas fa-times"></i>
              </button>
            </div>
            
            <div className="multi-call-tracker-content">
              <div className="call-items-grid">
                {activeCalls.map((call) => (
                  <div key={call.call_sid} className="call-item">
                    <div className="call-item-header">
                      <div className="call-item-icon">
                        {call.type === 'fire' && <i className="fas fa-fire"></i>}
                        {call.type === 'ambulance' && <i className="fas fa-ambulance"></i>}
                        {call.type === 'police' && <i className="fas fa-shield-alt"></i>}
                      </div>
                    </div>
                    
                    <div className="call-item-info">
                      <div className="call-item-type">{call.type.toUpperCase()}</div>
                      {call.priority && <div className="call-item-priority">Priority {call.priority}</div>}
                    </div>
                    
                    <div className="call-item-details">
                      <div className="call-item-status">
                        <div className="call-pulse-small">
                          <i className="fas fa-phone-alt"></i>
                        </div>
                        <span>Active</span>
                      </div>
                    </div>
                    
                    <div className="call-item-timer">
                      <i className="fas fa-clock"></i>
                      {Math.floor(call.duration / 60)}:{(call.duration % 60).toString().padStart(2, '0')}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="multi-call-actions">
                <button 
                  className="cancel-all-calls-btn" 
                  onClick={cancelAllEmergencyCalls}
                >
                  <i className="fas fa-phone-slash"></i>
                  Cancel All Calls
                </button>
              </div>
              
              <div className="multi-call-warning">
                ⚠️ These calls are being placed to emergency services. Only cancel if this was a mistake.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chatbot Section - Always Open */}
      <div className="chat-container open">
          <div className="chat-header">
            <span className="chat-header-text">
              <i className="fas fa-shield-alt"></i> Sri Lanka Emergency Assistant
            </span>
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
              onClick={() => quickQuestion(translations[currentLanguage].fireGuidance)}
            >
              <i className="fas fa-fire"></i> {translations[currentLanguage].fire}
            </button>
            <button
              className="emergency-button break-in-button"
              onClick={() => quickQuestion(translations[currentLanguage].breakInGuidance)}
            >
              <i className="fas fa-door-open"></i> {translations[currentLanguage].breakIn}
            </button>
            <button
              className="emergency-button medical-button"
              onClick={() => quickQuestion(translations[currentLanguage].medicalGuidance)}
            >
              <i className="fas fa-heartbeat"></i> {translations[currentLanguage].medical}
            </button>
            <button
              className="emergency-button police-button"
              onClick={() => quickQuestion(translations[currentLanguage].policeGuidance)}
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
              {isRecording ? `${recordingTime}s` : translations[currentLanguage].voiceBtn}
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