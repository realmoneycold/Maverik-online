import os
import soundfile as sf
import subprocess
try:
    from kokoro import KPipeline
except ImportError:
    KPipeline = None

class Mouth:
    def __init__(self, lang_code='a', voice='af_bella'):
        """
        Initializes the Kokoro TTS engine.
        lang_code='a' for American English.
        voice='af_bella' is a default voice.
        """
        self.lang_code = lang_code
        self.voice = voice
        self.current_process = None
        self._stop_flag = False
        
        if KPipeline:
            print(f"👄 Initializing Kokoro TTS with voice: {self.voice}")
            # Note: The first time this runs, it might download the model.
            self.pipeline = KPipeline(lang_code=self.lang_code, device='cpu')
        else:
            print("⚠️ Kokoro TTS not installed. Mouth will be silent.")
            self.pipeline = None

    def stop(self):
        """Immediately stops speaking by killing the audio player process."""
        self._stop_flag = True
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception:
                try:
                    self.current_process.kill()
                except:
                    pass
        print("🛑 MAVERIK stopped speaking.")

    def speak(self, text: str):
        """
        Synthesizes the text to speech and plays it.
        """
        if not self.pipeline:
            print(f"MAVERIK (Silent): {text}")
            return

        self._stop_flag = False
        try:
            generator = self.pipeline(
                text, 
                voice=self.voice, 
                speed=1
            )
            
            for i, (gs, ps, audio) in enumerate(generator):
                if self._stop_flag:
                    break
                    
                temp_filename = f'temp_speech_{i}.wav'
                # Kokoro uses 24000 Hz sample rate by default
                sf.write(temp_filename, audio, 24000)
                
                # Play the audio using aplay (Linux standard) non-blocking
                self.current_process = subprocess.Popen(["aplay", temp_filename], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                self.current_process.wait() # Wait for it to finish playing this chunk
                
                # Clean up
                try:
                    os.remove(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error speaking: {e}")
