/**
 * Live Mock Interview controller state machine
 */
class InterviewController {
    constructor(sessionId, questions) {
        this.sessionId = sessionId;
        this.questions = questions;
        this.currentIndex = 0;
        this.isProcessing = false;
        
        // DOM Elements
        this.questionCard = document.getElementById("question-card");
        this.questionText = document.getElementById("question-text");
        this.questionCategory = document.getElementById("question-category");
        this.questionProgress = document.getElementById("question-progress");
        this.progressBar = document.getElementById("progress-bar");
        
        this.transcriptContainer = document.getElementById("transcript-container");
        this.transcriptPreview = document.getElementById("transcript-preview");
        
        this.micBtn = document.getElementById("mic-btn");
        this.micPulse = document.getElementById("pulse-ring");
        this.soundWaves = document.getElementById("sound-waves");
        this.recordingStatus = document.getElementById("recording-status");
        
        this.submitBtn = document.getElementById("submit-btn");
        this.nextBtn = document.getElementById("next-btn");
        
        this.loader = document.getElementById("evaluation-loader");
        this.feedbackPanel = document.getElementById("feedback-panel");
        this.feedbackText = document.getElementById("feedback-text");
        this.scoreBadge = document.getElementById("score-badge");
        this.strengthsList = document.getElementById("strengths-list");
        this.weaknessesList = document.getElementById("weaknesses-list");
        this.modelAnswerText = document.getElementById("model-answer-text");

        this.init();
    }

    init() {
        // Setup Speech Manager Callbacks
        window.speechManager.onTranscriptUpdate = (text) => {
            this.transcriptPreview.textContent = text || "Speak now, transcribing in real-time...";
            if (text.trim().length > 5) {
                this.submitBtn.removeAttribute("disabled");
            } else {
                this.submitBtn.setAttribute("disabled", "true");
            }
        };

        window.speechManager.onRecordingStateChange = (isRecording) => {
            if (isRecording) {
                this.micBtn.classList.add("recording");
                this.micPulse.style.display = "block";
                this.soundWaves.classList.add("active");
                this.recordingStatus.textContent = "Listening... Click again to stop speaking.";
            } else {
                this.micBtn.classList.remove("recording");
                this.micPulse.style.display = "none";
                this.soundWaves.classList.remove("active");
                this.recordingStatus.textContent = "Click to Start Speaking";
            }
        };

        // Event Listeners
        this.micBtn.addEventListener("click", () => this.toggleRecording());
        this.submitBtn.addEventListener("click", () => this.submitAnswer());
        this.nextBtn.addEventListener("click", () => this.nextQuestion());

        // Load the first question
        this.renderCurrentQuestion();
    }

    renderCurrentQuestion() {
        const q = this.questions[this.currentIndex];
        
        // Update UI Text
        this.questionText.textContent = q.question_text;
        this.questionCategory.textContent = q.category;
        this.questionProgress.textContent = `Question ${this.currentIndex + 1} of ${this.questions.length}`;
        
        const progressPercentage = ((this.currentIndex + 1) / this.questions.length) * 100;
        this.progressBar.style.width = `${progressPercentage}%`;

        // Clear UI states
        window.speechManager.clearTranscript();
        this.transcriptPreview.textContent = "Your transcribed answer will appear here. Press the record button below to start.";
        this.submitBtn.setAttribute("disabled", "true");
        this.feedbackPanel.style.display = "none";
        this.nextBtn.style.display = "none";
        this.loader.style.display = "none";

        // Speak the question out loud
        this.playQuestionTTS(q.question_text);
    }

    playQuestionTTS(text) {
        this.recordingStatus.textContent = "Interviewer is speaking...";
        this.micBtn.setAttribute("disabled", "true");
        
        window.speechManager.speak(text, () => {
            // Callback when speaking finishes
            this.micBtn.removeAttribute("disabled");
            this.recordingStatus.textContent = "Interviewer finished. Click Mic to Start Speaking.";
            
            // Auto start recording if supported and user has allowed it
            // Safe fallback: let user click the mic themselves.
        });
    }

    toggleRecording() {
        if (this.isProcessing) return;
        
        if (window.speechManager.isRecording) {
            window.speechManager.stopListening();
        } else {
            window.speechManager.startListening();
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    async submitAnswer() {
        if (this.isProcessing) return;
        
        // Stop recording if active
        window.speechManager.stopListening();

        const answerText = this.transcriptPreview.textContent.trim();
        if (!answerText || answerText.startsWith("Your transcribed") || answerText.startsWith("Speak now")) {
            alert("Please provide a verbal response before submitting.");
            return;
        }

        // Get voice metrics before resetting/clearing
        const voiceMetrics = window.speechManager.getVoiceMetrics();
        console.log("Captured Voice Metrics:", voiceMetrics);

        const q = this.questions[this.currentIndex];
        const isLastQuestion = this.currentIndex === this.questions.length - 1;
        
        // UI Loading State
        this.isProcessing = true;
        this.submitBtn.setAttribute("disabled", "true");
        this.micBtn.setAttribute("disabled", "true");
        
        // Update loader text based on whether it is the final question
        const loaderTitle = this.loader.querySelector("h5");
        const loaderSubtitle = this.loader.querySelector("p");
        if (isLastQuestion) {
            loaderTitle.textContent = "Interview completed! Compiling final scorecard report...";
            loaderSubtitle.textContent = "Running Technical, Communication, and Vocal Confidence Agents in parallel...";
        } else {
            loaderTitle.textContent = "Saving response...";
            loaderSubtitle.textContent = "Preparing next question...";
        }
        this.loader.style.display = "block";
        
        // Cancel synthesis if active
        window.speechManager.cancelSpeaking();

        try {
            const csrfToken = this.getCookie("csrftoken") || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            const response = await fetch(`/api/sessions/${this.sessionId}/submit-answer/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    question_id: q.id,
                    answer: answerText,
                    voice_metrics: voiceMetrics
                })
            });

            if (!response.ok) {
                throw new Error("Failed to submit answer.");
            }

            // Defer analysis: Proceed immediately!
            if (!isLastQuestion) {
                this.currentIndex++;
                this.renderCurrentQuestion();
            } else {
                // Last question completed, redirect to report which compiles everything
                window.location.href = `/sessions/${this.sessionId}/report/`;
            }
        } catch (error) {
            console.error("Error submitting answer:", error);
            alert("There was an error saving your answer. Please try again.");
            this.submitBtn.removeAttribute("disabled");
            this.micBtn.removeAttribute("disabled");
            this.loader.style.display = "none";
        } finally {
            this.isProcessing = false;
        }
    }


    renderFeedback(data) {
        // Render score
        this.scoreBadge.textContent = `${data.evaluation.score}/100`;
        
        // Render Coach constructive feedback paragraph
        this.feedbackText.textContent = data.feedback;
        
        // Render strengths and weaknesses list
        this.strengthsList.innerHTML = "";
        data.evaluation.strengths.forEach(str => {
            const li = document.createElement("li");
            li.textContent = str;
            this.strengthsList.appendChild(li);
        });

        this.weaknessesList.innerHTML = "";
        data.evaluation.weaknesses.forEach(wk => {
            const li = document.createElement("li");
            li.textContent = wk;
            this.weaknessesList.appendChild(li);
        });

        // Render reference model answer
        this.modelAnswerText.textContent = data.evaluation.model_answer;

        // Display panel
        this.feedbackPanel.style.display = "block";
        
        // Speak feedback out loud (optional) or let the candidate read it. 
        // We'll read a short line: "Got it! Your score for this question is..."
        window.speechManager.speak(`Question completed. You scored ${data.evaluation.score} out of 100.`);

        // Setup navigation to next or finish
        if (this.currentIndex < this.questions.length - 1) {
            this.nextBtn.textContent = "Next Question";
        } else {
            this.nextBtn.textContent = "Finish & See Final Report";
        }
        this.nextBtn.style.display = "inline-block";
    }

    nextQuestion() {
        if (this.currentIndex < this.questions.length - 1) {
            this.currentIndex++;
            this.renderCurrentQuestion();
        } else {
            // Redirect to final report
            window.location.href = `/sessions/${this.sessionId}/report/`;
        }
    }
}
