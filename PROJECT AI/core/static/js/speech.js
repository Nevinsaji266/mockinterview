/**
 * Speech recognition (STT) and synthesis (TTS) manager class.
 */
class SpeechManager {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isRecording = false;
        this.transcriptBuffer = "";
        this.onTranscriptUpdate = null; // Callback when text is updated
        this.onRecordingStateChange = null; // Callback when recording starts/stops
        
        // Voice Analytics state variables
        this.startTime = null;
        this.recognitionConfidences = [];

        if (this.synthesis) {
            this.synthesis.onvoiceschanged = () => {
                this.synthesis.getVoices();
            };
        }

        this.initRecognition();
    }

    /**
     * Initializes the webkitSpeechRecognition API
     */
    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error("Speech Recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = "en-US";

        this.recognition.onstart = () => {
            this.isRecording = true;
            this.startTime = Date.now();
            this.recognitionConfidences = [];
            if (this.onRecordingStateChange) this.onRecordingStateChange(true);
        };

        this.recognition.onend = () => {
            this.isRecording = false;
            if (this.onRecordingStateChange) this.onRecordingStateChange(false);
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.isRecording = false;
            if (this.onRecordingStateChange) this.onRecordingStateChange(false);
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = "";
            let finalTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    this.transcriptBuffer += event.results[i][0].transcript + " ";
                    if (event.results[i][0].confidence) {
                        this.recognitionConfidences.push(event.results[i][0].confidence);
                    }
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const currentFullText = this.transcriptBuffer + interimTranscript;
            if (this.onTranscriptUpdate) {
                this.onTranscriptUpdate(currentFullText.trim());
            }
        };
    }

    /**
     * Start speech recording
     */
    startListening() {
        if (!this.recognition) {
            alert("Speech recognition is not supported or initialized in this browser.");
            return;
        }
        if (this.isRecording) return;

        this.transcriptBuffer = "";
        this.startTime = Date.now();
        this.recognitionConfidences = [];
        try {
            // Cancel any ongoing speaking before listening
            this.synthesis.cancel();
            this.recognition.start();
        } catch (e) {
            console.error("Error starting speech recognition:", e);
        }
    }

    /**
     * Stop speech recording
     */
    stopListening() {
        if (!this.recognition || !this.isRecording) return;
        this.recognition.stop();
    }

    /**
     * Clear the current transcripts
     */
    clearTranscript() {
        this.transcriptBuffer = "";
        this.startTime = null;
        this.recognitionConfidences = [];
        if (this.onTranscriptUpdate) this.onTranscriptUpdate("");
    }

    /**
     * Exposes voice metrics gathered during the current question's recording
     */
    getVoiceMetrics() {
        const durationSeconds = this.startTime ? (Date.now() - this.startTime) / 1000 : 0;
        const text = this.transcriptBuffer.trim();
        const wordCount = text ? text.split(/\s+/).length : 0;
        
        // Words Per Minute (Pacing)
        const wordsPerMinute = durationSeconds > 0 ? Math.round((wordCount / durationSeconds) * 60) : 0;
        
        // Average transcription confidence
        const avgConfidence = this.recognitionConfidences.length > 0 
            ? this.recognitionConfidences.reduce((a, b) => a + b, 0) / this.recognitionConfidences.length
            : 0.90;
            
        // Count filler words
        const fillerList = ["um", "uh", "ah", "like", "basically", "actually", "so"];
        let fillerCount = 0;
        if (text) {
            const words = text.toLowerCase().split(/\s+/);
            words.forEach(w => {
                const cleanWord = w.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "");
                if (fillerList.includes(cleanWord)) {
                    fillerCount++;
                }
            });
            // Also search for word sequence "you know"
            const youKnowCount = (text.toLowerCase().match(/\byou know\b/g) || []).length;
            fillerCount += youKnowCount;
        }

        return {
            duration_seconds: Math.round(durationSeconds * 10) / 10,
            word_count: wordCount,
            words_per_minute: wordsPerMinute,
            average_confidence: Math.round(avgConfidence * 100),
            filler_words_count: fillerCount
        };

    }

    /**
     * Speaks the provided text using the Web Speech Synthesis API.
     * Triggers onEnd when speaking completes.
     */
    speak(text, onEnd = null) {
        if (!this.synthesis) {
            if (onEnd) onEnd();
            return;
        }

        // Cancel current speaking
        try {
            this.synthesis.cancel();
        } catch (e) {
            console.warn("Speech Synthesis cancel failed:", e);
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        
        // Prioritized voice selection logic
        const voices = this.synthesis.getVoices();
        const englishVoices = voices.filter(v => v.lang.startsWith("en-") || v.lang.startsWith("en_"));
        
        let selectedVoice = null;
        const priorityKeywords = ["natural", "neural", "online", "google", "guy", "aria", "jenny"];
        for (const kw of priorityKeywords) {
            selectedVoice = englishVoices.find(v => v.name.toLowerCase().includes(kw));
            if (selectedVoice) break;
        }
        
        if (!selectedVoice && englishVoices.length > 0) {
            selectedVoice = englishVoices[0];
        }
        
        if (selectedVoice) {
            utterance.voice = selectedVoice;
            console.log("Selected Speech Voice:", selectedVoice.name);
        }

        // Slightly slower rate (0.93) to make it sound premium, articulate, and paced like a human interviewer.
        utterance.rate = 0.93;
        utterance.pitch = 1.05; // slightly higher pitch for clarity

        if (onEnd) {
            utterance.onend = () => {
                onEnd();
            };
            utterance.onerror = (e) => {
                console.error("TTS utterance error:", e);
                onEnd();
            };
        }

        try {
            this.synthesis.speak(utterance);
        } catch (e) {
            console.error("Speech Synthesis failed to speak:", e);
            if (onEnd) onEnd();
        }
    }

    /**
     * Stop speaking immediately
     */
    cancelSpeaking() {
        if (this.synthesis) {
            try {
                this.synthesis.cancel();
            } catch (e) {
                console.warn("Speech Synthesis cancel failed:", e);
            }
        }
    }

}

// Instantiate globally
window.speechManager = new SpeechManager();

