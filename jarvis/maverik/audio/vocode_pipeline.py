import asyncio
from typing import AsyncGenerator
import logging

from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.input_device.microphone_input import MicrophoneInput
from maverik.audio.aplay_output import AplayOutputDevice
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.agent.base_agent import RespondAgent, GeneratedResponse

from maverik.audio.vocode_custom import LocalWhisperTranscriber, LocalWhisperConfig
from maverik.audio.vocode_custom import KokoroSynthesizer, KokoroSynthesizerConfig
from maverik.brain.agent_brain import AgentBrain
from maverik.brain.router import analyze_intent

logging.getLogger("vocode").setLevel(logging.INFO)

class MaverikAgentConfig(AgentConfig, type="agent_maverik"):
    # Disable Vocode's built-in "hang up" feature if the user is silent.
    # An ambient desktop assistant should never hang up!
    allowed_idle_time_seconds: float = 31536000.0  # 1 year

class MaverikAgent(RespondAgent[MaverikAgentConfig]):
    """Custom Vocode Agent wrapping our LangGraph brain and Semantic Router."""
    def __init__(self, agent_config: MaverikAgentConfig):
        super().__init__(agent_config)
        self.brain = AgentBrain()

    async def generate_response(
        self,
        human_input: str,
        conversation_id: str,
        is_interrupt: bool = False,
        bot_was_in_medias_res: bool = False,
    ) -> AsyncGenerator[GeneratedResponse, None]:
        print(f"\n🗣️ YOU: {human_input}")
        
        # 1. Route Intent
        intent = analyze_intent(human_input)
        
        # 2. Think and Act (Native Async - can be cancelled if user speaks over it!)
        try:
            response = await self.brain.athink_and_act(human_input, intent=intent)
        except asyncio.CancelledError:
            return
            
        print(f"🤖 MAVERIK: {response}")
        
        # 3. Yield to Vocode's TTS Synthesizer
        # is_interruptible=True enables the native 'barge-in' feature!
        yield GeneratedResponse(message=BaseMessage(text=response), is_interruptible=True)

async def run_vocode_pipeline():
    print("🎙️ Initializing Audio Devices...")
    # Whisper STRICTLY requires 16000 Hz audio.
    microphone_input = MicrophoneInput.from_default_device(sampling_rate=16000)
    # Kokoro STRICTLY outputs 24000 Hz audio. We use native Linux aplay to bypass sounddevice bugs!
    speaker_output = AplayOutputDevice(sampling_rate=24000)
    
    print("🎙️ Loading Offline Transcriber (Whisper)...")
    transcriber = LocalWhisperTranscriber(
        LocalWhisperConfig(
            sampling_rate=microphone_input.sampling_rate,
            audio_encoding=microphone_input.audio_encoding,
            chunk_size=microphone_input.chunk_size,
            model_size="tiny.en"
        )
    )
    
    print("👄 Loading Offline Synthesizer (Kokoro)...")
    synthesizer = KokoroSynthesizer(
        KokoroSynthesizerConfig(
            sampling_rate=speaker_output.sampling_rate,
            audio_encoding=speaker_output.audio_encoding,
            voice="af_bella"
        )
    )
    
    print("🧠 Booting LangGraph Agent...")
    agent = MaverikAgent(MaverikAgentConfig(initial_message=None))
    
    # The heart of Phase 4: Real-time Streaming Conversation
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=transcriber,
        agent=agent,
        synthesizer=synthesizer,
    )
    
    print("\n✅ MAVERIK Vocode is fully operational! Speak into the microphone.")
    await conversation.start()
    
    # Continuously pump audio from the microphone into the Vocode conversation
    async def process_audio():
        while conversation.is_active():
            chunk = await microphone_input.get_audio()
            conversation.receive_audio(chunk)
            
    # Run the audio pump and keep the main loop alive
    asyncio.create_task(process_audio())
    
    try:
        # Keep the streaming loop alive while the conversation is active
        while conversation.is_active():
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Vocode pipeline...")
    finally:
        await conversation.terminate()

if __name__ == "__main__":
    asyncio.run(run_vocode_pipeline())
