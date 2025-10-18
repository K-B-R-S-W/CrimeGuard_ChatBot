/**
 * Speech Service for ElevenLabs STT and Browser TTS
 * Handles speech-to-text transcription and text-to-speech synthesis
 */

const ELEVENLABS_API_KEY = process.env.REACT_APP_ELEVENLABS_API_KEY || '';
const TTS_SPEED = parseFloat(process.env.REACT_APP_TTS_SPEED || '1.3');

/**
 * Transcribe audio using ElevenLabs Speech-to-Text API
 * @param audioBlob - The audio blob to transcribe
 * @returns Promise<string> - The transcribed text
 */
export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  try {
    console.log('Starting ElevenLabs transcription...');
    
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    formData.append('model_id', 'scribe_v1');
    
    const response = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
      method: 'POST',
      headers: {
        'xi-api-key': ELEVENLABS_API_KEY,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('ElevenLabs API Error:', errorData);
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    const data = await response.json();
    const transcription = data.text || '';
    
    console.log('Transcription successful:', transcription);
    return transcription.trim();
  } catch (error) {
    console.error('Error during transcription:', error);
    throw new Error('Failed to transcribe audio. Please try again.');
  }
}

/**
 * Ensure voices are loaded
 */
function ensureVoicesLoaded(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      resolve(voices);
      return;
    }
    
    // Wait for voices to load
    window.speechSynthesis.onvoiceschanged = () => {
      const loadedVoices = window.speechSynthesis.getVoices();
      resolve(loadedVoices);
    };
    
    // Timeout after 2 seconds
    setTimeout(() => {
      resolve(window.speechSynthesis.getVoices());
    }, 2000);
  });
}

/**
 * Fallback TTS using backend gTTS service for Sinhala/Tamil
 * Optimized with timeout and better error handling
 * @param text Text to speak
 * @param language Language code ('en', 'si', 'ta')
 * @param speed Speech rate multiplier
 */
async function speakWithBackendTTS(text: string, language: string, speed: number): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      console.log(`Using backend TTS for ${language} - Generating audio...`);
      const startTime = Date.now();
      
      // Call backend TTS endpoint with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          language: language
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Backend TTS failed: ${response.statusText}`);
      }
      
      // Get audio blob
      const audioBlob = await response.blob();
      const generationTime = Date.now() - startTime;
      console.log(`Audio generated in ${generationTime}ms`);
      
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audio.playbackRate = speed;
      
      audio.oncanplaythrough = () => {
        console.log('Audio ready to play');
      };
      
      audio.onended = () => {
        const totalTime = Date.now() - startTime;
        console.log(`Backend TTS finished (total: ${totalTime}ms)`);
        URL.revokeObjectURL(audioUrl); // Clean up
        resolve();
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        URL.revokeObjectURL(audioUrl); // Clean up
        reject(new Error('Failed to play audio'));
      };
      
      await audio.play();
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('Backend TTS timeout after 10 seconds');
        reject(new Error('TTS generation timeout'));
      } else {
        console.error('Backend TTS error:', error);
        reject(error);
      }
    }
  });
}

/**
 * Convert text to speech using browser's Speech Synthesis API
 * Falls back to Google TTS for Sinhala/Tamil if no browser voice available
 * @param text - The text to convert to speech
 * @param language - Language code ('en', 'si', 'ta')
 * @param speed - Playback speed (default: 1.3)
 */
export async function speakText(
  text: string,
  language: string = 'en',
  speed: number = TTS_SPEED
): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      console.log(`Speaking text in ${language} at ${speed}x speed:`, text.substring(0, 50));
      
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      // Small delay to ensure cancel completes
      await new Promise(r => setTimeout(r, 100));
      
      // Ensure voices are loaded
      const voices = await ensureVoicesLoaded();
      console.log(`Available voices: ${voices.length}`);
      
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Map language codes to browser speech synthesis codes
      const langMap: { [key: string]: string } = {
        'en': 'en-US',
        'si': 'si-LK',  // Sinhala (Sri Lanka)
        'ta': 'ta-IN',  // Tamil (India)
      };
      
      const targetLang = langMap[language] || 'en-US';
      utterance.lang = targetLang;
      utterance.rate = speed;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // Try to find a voice that matches the language
      // First try exact match, then try language prefix
      let matchingVoice = voices.find(voice => voice.lang === targetLang);
      
      if (!matchingVoice) {
        const langPrefix = targetLang.split('-')[0];
        matchingVoice = voices.find(voice => voice.lang.startsWith(langPrefix));
      }
      
      // For Sinhala and Tamil, if no matching voice, use backend TTS instead
      if (!matchingVoice && (language === 'si' || language === 'ta')) {
        console.log(`No ${language} voice found in browser, using backend TTS`);
        try {
          await speakWithBackendTTS(text, language, speed);
          return;
        } catch (error) {
          console.error('Backend TTS failed:', error);
          // Continue with English voice as last resort
          matchingVoice = voices.find(voice => voice.lang.startsWith('en'));
        }
      }
      
      if (matchingVoice) {
        utterance.voice = matchingVoice;
        console.log('Using voice:', matchingVoice.name, matchingVoice.lang);
      } else {
        console.log('No matching voice found, using default voice');
        // Use first available voice as fallback
        if (voices.length > 0) {
          utterance.voice = voices[0];
          console.log('Using fallback voice:', voices[0].name);
        }
      }
      
      utterance.onstart = () => {
        console.log('Speech started');
      };
      
      utterance.onend = () => {
        console.log('Speech finished successfully');
        resolve();
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        reject(new Error(`Speech synthesis failed: ${event.error}`));
      };
      
      // Speak the utterance
      console.log('Starting speech synthesis...');
      window.speechSynthesis.speak(utterance);
      
      // Fallback: if speech doesn't start in 3 seconds, reject
      setTimeout(() => {
        if (!window.speechSynthesis.speaking && !window.speechSynthesis.pending) {
          console.warn('Speech did not start within timeout');
          resolve(); // Resolve anyway to not block the flow
        }
      }, 3000);
      
    } catch (error) {
      console.error('Error during speech synthesis:', error);
      reject(error);
    }
  });
}

/**
 * Stop any ongoing speech
 */
export function stopSpeaking(): void {
  window.speechSynthesis.cancel();
}

/**
 * Check if speech synthesis is supported
 */
export function isSpeechSynthesisSupported(): boolean {
  return 'speechSynthesis' in window;
}

/**
 * Get available voices (call after voices are loaded)
 */
export function getAvailableVoices(): SpeechSynthesisVoice[] {
  return window.speechSynthesis.getVoices();
}

// Load voices when they become available
if (isSpeechSynthesisSupported()) {
  // Voices might not be loaded immediately
  window.speechSynthesis.onvoiceschanged = () => {
    const voices = getAvailableVoices();
    console.log('Speech synthesis voices loaded:', voices.length);
    
    // Log available Sinhala and Tamil voices
    const sinhalaVoices = voices.filter(v => v.lang.startsWith('si'));
    const tamilVoices = voices.filter(v => v.lang.startsWith('ta'));
    
    if (sinhalaVoices.length > 0) {
      console.log('Sinhala voices available:', sinhalaVoices.map(v => v.name));
    }
    if (tamilVoices.length > 0) {
      console.log('Tamil voices available:', tamilVoices.map(v => v.name));
    }
  };
}
