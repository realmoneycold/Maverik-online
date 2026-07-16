from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size="tiny.en"):
        """
        Initializes the Faster-Whisper model.
        Using 'tiny.en' because it provides near-instantaneous transcription for voice commands.
        """
        print(f"Loading Speech-to-Text Model ({model_size})...")
        
        try:
            # Temporarily using CPU to avoid libcublas linker errors
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            print("🚀 Transcriber is utilizing CPU.")
        except Exception as e:
            # Fallback to CPU if CUDA libraries are not perfectly configured yet
            print(f"⚠️ GPU init failed ({e}). Falling back to CPU for transcription.")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_file: str) -> str:
        """
        Transcribes the audio file and returns the text.
        """
        # Beam size 5 provides a good balance between accuracy and speed
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        
        # Combine all segments of speech into a single string
        text = "".join([segment.text for segment in segments]).strip()
        return text
