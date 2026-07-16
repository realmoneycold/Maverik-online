/**
 * Voice input (Web Speech API) and audio output (AudioContext) for JARVIS.
 */

// ---------------------------------------------------------------------------
// Speech Recognition
// ---------------------------------------------------------------------------

export interface VoiceInput {
  start(): void;
  stop(): void;
  pause(): void;
  resume(): void;
}

export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (msg: string) => void
): VoiceInput {
  let shouldListen = false;
  let isRecording = false;
  let isPaused = false;
  let mediaRecorder: MediaRecorder | null = null;
  let audioChunks: Blob[] = [];
  
  let audioCtx: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  let stream: MediaStream | null = null;
  let silenceTimer: ReturnType<typeof setTimeout> | null = null;

  async function startRecording() {
    if (isRecording || isPaused || !shouldListen) return;

    try {
      if (!stream) {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      if (!audioCtx) {
        audioCtx = new AudioContext();
        const source = audioCtx.createMediaStreamSource(stream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);
      }

      const pcmData = new Uint8Array(analyser!.frequencyBinCount);

      function checkSilence() {
        if (!isRecording) return; // stop loop
        
        analyser!.getByteFrequencyData(pcmData);
        let sum = 0;
        for (let i = 0; i < pcmData.length; i++) sum += pcmData[i];
        let average = sum / pcmData.length;
        
        // Threshold for speaking
        if (average > 10) { 
          if (silenceTimer) {
             clearTimeout(silenceTimer);
             silenceTimer = null;
          }
        } else {
          // Silence detected
          if (!silenceTimer && isRecording) {
             silenceTimer = setTimeout(() => {
                if (isRecording && mediaRecorder?.state === 'recording') {
                   mediaRecorder.stop();
                }
             }, 1200); // Wait 1.2s of silence before stopping chunk
          }
        }
        
        requestAnimationFrame(checkSilence);
      }

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };
      
      mediaRecorder.onstop = () => {
        isRecording = false;
        
        if (audioChunks.length > 0) {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          audioChunks = [];
          
          // Send to backend via a global hook that main.ts will set up
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = () => {
            const base64data = (reader.result as string).split(',')[1];
            // @ts-ignore
            if (window.sendAudioInput) {
              // @ts-ignore
              window.sendAudioInput(base64data);
            }
          };
        }
        
        // Restart recording if we should still be listening
        if (shouldListen && !isPaused) {
           setTimeout(() => {
              if (shouldListen && !isPaused && !isRecording) {
                 startRecording();
              }
           }, 100);
        }
      };

      isRecording = true;
      mediaRecorder.start();
      checkSilence();
      
    } catch (e) {
       console.error("Microphone error:", e);
       onError("Microphone access denied or error.");
       shouldListen = false;
    }
  }

  return {
    start() {
      shouldListen = true;
      isPaused = false;
      startRecording();
    },
    stop() {
      shouldListen = false;
      isPaused = false;
      if (isRecording && mediaRecorder?.state === 'recording') {
        mediaRecorder.stop();
      }
    },
    pause() {
      isPaused = true;
      if (isRecording && mediaRecorder?.state === 'recording') {
        mediaRecorder.stop();
      }
    },
    resume() {
      isPaused = false;
      if (shouldListen && !isRecording) {
        startRecording();
      }
    },
  };
}

// ---------------------------------------------------------------------------
// Audio Player
// ---------------------------------------------------------------------------

export interface AudioPlayer {
  enqueue(base64: string): Promise<void>;
  stop(): void;
  getAnalyser(): AnalyserNode;
  onFinished(cb: () => void): void;
}

export function createAudioPlayer(): AudioPlayer {
  const audioCtx = new AudioContext();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  analyser.smoothingTimeConstant = 0.8;
  analyser.connect(audioCtx.destination);

  const queue: AudioBuffer[] = [];
  let isPlaying = false;
  let currentSource: AudioBufferSourceNode | null = null;
  let finishedCallback: (() => void) | null = null;

  function playNext() {
    if (queue.length === 0) {
      isPlaying = false;
      currentSource = null;
      finishedCallback?.();
      return;
    }

    isPlaying = true;
    const buffer = queue.shift()!;
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(analyser);
    currentSource = source;

    source.onended = () => {
      if (currentSource === source) {
        playNext();
      }
    };

    source.start();
  }

  return {
    async enqueue(base64: string) {
      // Resume audio context (browser autoplay policy)
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      try {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }
        const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer.slice(0));
        queue.push(audioBuffer);
        if (!isPlaying) playNext();
      } catch (err) {
        console.error("[audio] decode error:", err);
        // Skip bad audio, continue
        if (!isPlaying && queue.length > 0) playNext();
      }
    },

    stop() {
      queue.length = 0;
      if (currentSource) {
        try {
          currentSource.stop();
        } catch {
          // Already stopped
        }
        currentSource = null;
      }
      isPlaying = false;
    },

    getAnalyser() {
      return analyser;
    },

    onFinished(cb: () => void) {
      finishedCallback = cb;
    },
  };
}
