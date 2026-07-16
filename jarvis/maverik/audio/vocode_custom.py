import asyncio
import numpy as np
from typing import AsyncGenerator, Optional

from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.transcriber.base_transcriber import BaseAsyncTranscriber, Transcription
from vocode.streaming.models.transcriber import TranscriberConfig
from vocode.streaming.models.audio import AudioEncoding
from vocode.streaming.models.message import BaseMessage

from maverik.audio.mouth import Mouth
from maverik.audio.transcriber import Transcriber as WhisperTranscriber

class KokoroSynthesizerConfig(SynthesizerConfig, type="synthesizer_kokoro"):
    voice: str = "af_bella"

class KokoroSynthesizer(BaseSynthesizer[KokoroSynthesizerConfig]):
    """Custom Vocode Synthesizer wrapping our local Kokoro TTS engine."""
    def __init__(self, synthesizer_config: KokoroSynthesizerConfig):
        super().__init__(synthesizer_config)
        self.mouth = Mouth(voice=synthesizer_config.voice)
        
    async def create_speech(
        self,
        message: BaseMessage,
        chunk_size: int,
        is_first_text_chunk: bool = False,
        is_sole_text_chunk: bool = False,
    ) -> SynthesisResult:
        if not self.mouth.pipeline:
            raise RuntimeError("Kokoro is not installed.")
            
        # Vocode passes a BaseMessage object. We need to extract the raw text string.
        text_to_speak = message.text
        
        # Offload the heavy TTS generation to a background thread so it doesn't block Vocode
        def generate_audio():
            try:
                print(f"[Kokoro] Starting generation for: {text_to_speak[:30]}...", flush=True)
                chunks = list(self.mouth.pipeline(text_to_speak, voice=self.synthesizer_config.voice, speed=1))
                print(f"[Kokoro] Successfully generated {len(chunks)} raw audio chunks.", flush=True)
                return chunks
            except Exception as e:
                print(f"❌ [Kokoro] Error during generation: {e}")
                return []
            
        async def chunk_generator() -> AsyncGenerator[SynthesisResult.ChunkResult, None]:
            # We await the generation INSIDE the generator so create_speech returns instantly!
            chunks_data = await asyncio.to_thread(generate_audio)
            
            total_bytes = 0
            for i, (gs, ps, audio) in enumerate(chunks_data):
                # Kokoro returns PyTorch Tensors. Convert to NumPy floats (-1.0 to 1.0).
                if hasattr(audio, 'cpu'):
                    audio = audio.cpu().numpy()
                elif hasattr(audio, 'numpy'):
                    audio = audio.numpy()
                    
                # Convert to 16-bit PCM bytes for Vocode
                audio_int16 = (audio * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                total_bytes += len(audio_bytes)
                
                # Stream the bytes in the exact chunk size Vocode asks for
                for j in range(0, len(audio_bytes), chunk_size):
                    chunk = audio_bytes[j:j+chunk_size]
                    is_last_chunk = (i == len(chunks_data) - 1) and (j + chunk_size >= len(audio_bytes))
                    yield SynthesisResult.ChunkResult(chunk, is_last_chunk)
            print(f"[Kokoro] Finished yielding chunks. Total PCM bytes: {total_bytes}", flush=True)

        return SynthesisResult(chunk_generator(), lambda seconds: message.text)

class LocalWhisperConfig(TranscriberConfig, type="transcriber_local_whisper"):
    model_size: str = "tiny.en"

class LocalWhisperTranscriber(BaseAsyncTranscriber[LocalWhisperConfig]):
    """Custom Vocode Transcriber wrapping our local Faster-Whisper engine."""
    def __init__(self, transcriber_config: LocalWhisperConfig):
        super().__init__(transcriber_config)
        self.transcriber = WhisperTranscriber(model_size=transcriber_config.model_size)
        self.audio_buffer = bytearray()

    async def _run_loop(self):
        import audioop
        silence_threshold = 250  # Lowered so it can hear the user's quiet microphone
        silence_chunks = 0
        is_speaking = False
        
        while True:
            try:
                chunk = await asyncio.wait_for(self.input_queue.get(), timeout=0.1)
                
                # Calculate volume
                rms = audioop.rms(chunk, 2)
                
                if rms > silence_threshold:
                    is_speaking = True
                    silence_chunks = 0
                    self.audio_buffer.extend(chunk)
                elif is_speaking:
                    silence_chunks += 1
                    self.audio_buffer.extend(chunk)
                    
                    # If we have 2 seconds of silence, the user finished speaking!
                    if silence_chunks > 20:
                        audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        # vad_filter=True completely eliminates 'Ooh ooh ooh' and 'Mm-hmm' hallucinations!
                        segments, _ = await asyncio.to_thread(
                            self.transcriber.model.transcribe, audio_data, beam_size=5, vad_filter=True
                        )
                        
                        text = "".join([s.text for s in segments]).strip()
                        if text:
                            self.output_queue.put_nowait(Transcription(message=text, confidence=1.0, is_final=True))
                        
                        self.audio_buffer.clear()
                        is_speaking = False
                        silence_chunks = 0
                        
            except asyncio.TimeoutError:
                pass
