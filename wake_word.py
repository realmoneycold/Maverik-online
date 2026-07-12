import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model

# For our initial test, we will use the pre-trained "hey_jarvis" model.
# Later, we can train a custom "Hey Maverik" model!
WAKE_WORD_MODEL = "hey_jarvis"

def main():
    print(f"Loading wake word model: '{WAKE_WORD_MODEL}'...")
    
    # We manually downloaded the model to avoid the 5-minute hanging download
    # Load it directly from the current folder!
    oww_model = Model(wakeword_models=["./hey_jarvis_v0.1.tflite"])

    # Set up PyAudio parameters (OpenWakeWord requires 16kHz, 16-bit audio)
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280

    audio = pyaudio.PyAudio()
    
    print("Opening microphone stream...")
    mic_stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

    print("\n🎧 MAVERIK is listening in the background...")
    print("🗣️  Say 'Hey Jarvis' to trigger the system! (Press Ctrl+C to exit)\n")

    try:
        while True:
            # 1. Read audio data from microphone
            # exception_on_overflow=False prevents crashes if we process too slowly
            mic_data = mic_stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(mic_data, dtype=np.int16)

            # 2. Feed audio to the wake word model
            oww_model.predict(audio_data)

            # 3. Check predictions for the specific model
            for mdl in oww_model.prediction_buffer.keys():
                scores = list(oww_model.prediction_buffer[mdl])
                
                # If confidence score is high enough (0.5 is a good default threshold)
                if scores[-1] > 0.5:
                    print(f"\n⚡ [ACTIVATED] WAKE WORD DETECTED: {mdl}!")
                    
                    # Prevent multiple rapid triggers from the same utterance
                    oww_model.reset()
                    
                    # TODO: Next step will be passing control to Silero VAD to record the command!
                    
    except KeyboardInterrupt:
        print("\nStopping listening...")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()
