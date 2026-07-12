import subprocess
import queue
import threading
from typing import Optional
from vocode.streaming.output_device.base_output_device import BaseOutputDevice
from vocode.streaming.models.audio import AudioEncoding

class AplayOutputDevice(BaseOutputDevice):
    """
    A custom output device that streams raw PCM audio directly to the Linux `aplay` utility.
    This completely bypasses python-sounddevice and PipeWire/PulseAudio sink routing issues,
    which commonly cause silent audio on Linux laptops.
    """
    def __init__(self, sampling_rate: int = 24000):
        super().__init__(sampling_rate, AudioEncoding.LINEAR16)
        self.process = None
        self.queue = queue.Queue()
        self.active = False
        self.worker_thread = None

    def start(self):
        self.active = True
        # Launch aplay expecting raw 16-bit little-endian PCM stream
        self.process = subprocess.Popen(
            [
                "aplay",
                "-f", "S16_LE",
                "-c", "1",
                "-r", str(self.sampling_rate),
                "-t", "raw",
                "-"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL
            # stderr is left visible to debug aplay errors!
        )
        self.worker_thread = threading.Thread(target=self._pump_audio, daemon=True)
        self.worker_thread.start()

    def _pump_audio(self):
        while self.active:
            try:
                # Block until a chunk is available (timeout allows checking self.active)
                chunk = self.queue.get(timeout=0.1)
                if self.process and self.process.stdin:
                    self.process.stdin.write(chunk)
                    self.process.stdin.flush()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error playing audio chunk via aplay: {e}")
                break

    def consume_nonblocking(self, chunk: bytes):
        self.queue.put(chunk)

    def terminate(self):
        self.active = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.kill()
            except Exception:
                pass
