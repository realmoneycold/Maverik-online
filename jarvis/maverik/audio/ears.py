import pyaudio
import numpy as np
import torch
import wave
from openwakeword.model import Model

class Ears:
    def __init__(self, wake_word_model="./hey_jarvis_v0.1.tflite"):
        self.wake_word_model = wake_word_model
        
        # Audio hardware constants
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1280       # OpenWakeWord chunk size
        self.VAD_CHUNK = 512    # Silero VAD chunk size (512 is best for 16kHz)
        
        print(f"Loading Wake Word Engine ({self.wake_word_model})...")
        self.oww_model = Model(wakeword_models=[self.wake_word_model])
        
        print("Loading Audio Gater (Silero VAD)...")
        # Load Silero VAD locally to bypass GitHub API rate limits
        self.vad_model, self.vad_utils = torch.hub.load(
            repo_or_dir='./maverik/audio/silero-vad',
            model='silero_vad',
            source='local',
            force_reload=False,
            trust_repo=True
        )
        self.vad_model.eval()

        self.audio = pyaudio.PyAudio()

    def listen_for_wake_word(self):
        """Continuously listens for the wake word in the background."""
        mic_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        print("\n🎧 MAVERIK is listening in the background...")
        
        while True:
            audio_data = np.frombuffer(mic_stream.read(self.CHUNK, exception_on_overflow=False), dtype=np.int16)
            self.oww_model.predict(audio_data)
            
            for mdl in self.oww_model.prediction_buffer.keys():
                scores = list(self.oww_model.prediction_buffer[mdl])
                if scores[-1] > 0.5:
                    print(f"\n⚡ WAKE WORD DETECTED: {mdl}!")
                    self.oww_model.reset()
                    
                    # Stop the wake word stream
                    mic_stream.stop_stream()
                    mic_stream.close()
                    
                    # Transition seamlessly to recording the command
                    return self.record_command()

    def record_command(self):
        """Records audio until the user stops speaking."""
        print("🎙️  Recording your command... Speak now!")
        
        mic_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.VAD_CHUNK
        )
        
        recorded_frames = []
        silence_chunks = 0
        # 1.5 seconds of pure silence will trigger the stop (16000 rate / 512 chunk size = ~31 chunks per second)
        max_silence_chunks = int((16000 / self.VAD_CHUNK) * 1.5) 
        speech_started = False
        
        while True:
            audio_chunk = mic_stream.read(self.VAD_CHUNK, exception_on_overflow=False)
            recorded_frames.append(audio_chunk)
            
            # Convert raw audio to float32 tensor for Silero VAD
            audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            tensor_chunk = torch.from_numpy(audio_float32)
            
            # Calculate the probability that this chunk contains human speech
            speech_prob = self.vad_model(tensor_chunk, self.RATE).item()
            
            if speech_prob > 0.5:
                # We heard a voice!
                speech_started = True
                silence_chunks = 0
            elif speech_started:
                # We are waiting for them to stop talking
                silence_chunks += 1
                
            if speech_started and silence_chunks > max_silence_chunks:
                print("🛑 Silence detected. Saving command.")
                break
                
        mic_stream.stop_stream()
        mic_stream.close()
        
        # Save the recording to a temporary file
        filename = "command.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(recorded_frames))
        wf.close()
        
        return filename

    def cleanup(self):
        self.audio.terminate()
