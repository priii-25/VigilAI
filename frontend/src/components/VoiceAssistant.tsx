import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { api } from '../lib/api';

// Type definition for SpeechRecognition
declare global {
    interface Window {
        webkitSpeechRecognition: any;
        SpeechRecognition: any;
    }
}

const VoiceAssistant: React.FC = () => {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                recognitionRef.current = new SpeechRecognition();
                recognitionRef.current.continuous = false;
                recognitionRef.current.interimResults = false;
                recognitionRef.current.lang = 'en-US';

                recognitionRef.current.onresult = async (event: any) => {
                    const transcript = event.results[0][0].transcript;
                    console.log('Voice Query:', transcript);
                    handleVoiceQuery(transcript);
                };

                recognitionRef.current.onerror = (event: any) => {
                    console.error('Speech recognition error', event.error);
                    setIsListening(false);
                    toast.error("Voice recognition failed. Try again.");
                };

                recognitionRef.current.onend = () => {
                    setIsListening(false);
                };
            }
        }
    }, []);

    const handleVoiceQuery = async (query: string) => {
        toast.loading(`Thinking: "${query}"...`, { id: 'voice-query' });

        try {
            // Create axios instance or use fetch if api.ts doesn't have it yet
            // Assuming api.ts has a generic request or we add it. 
            // For now using fetch to match likely auth header needs or minimal deps

            const token = localStorage.getItem('token'); // Simplistic token grab

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error('Failed to get answer');

            const data = await response.json();

            toast.success("Answer received!", { id: 'voice-query' });
            speakResponse(data.answer);

        } catch (error) {
            console.error(error);
            toast.error("Failed to process voice query", { id: 'voice-query' });
        }
    };

    const speakResponse = (text: string) => {
        if ('speechSynthesis' in window) {
            setIsSpeaking(true);
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.onend = () => setIsSpeaking(false);
            window.speechSynthesis.speak(utterance);
        } else {
            toast("Text-to-speech not supported.");
        }
    };

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            setIsListening(true);
            try {
                recognitionRef.current?.start();
                toast("Listening... Speak now 🎙️");
            } catch (e) {
                console.error(e);
            }
        }
    };

    if (!recognitionRef.current) return null; // Don't render if not supported

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
            {isSpeaking && (
                <div className="bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg mb-2 animate-pulse">
                    🔊 Speaking...
                </div>
            )}

            <button
                onClick={toggleListening}
                className={`w-16 h-16 rounded-full shadow-2xl flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 ${isListening
                        ? 'bg-red-500 animate-pulse ring-4 ring-red-300'
                        : 'bg-indigo-600 hover:bg-indigo-700'
                    }`}
                title="Ask VigilAI"
            >
                <span className="text-3xl">
                    {isListening ? '🛑' : '🎙️'}
                </span>
            </button>
        </div>
    );
};

export default VoiceAssistant;
