import asyncio
import os
import queue
import sys
import threading
from typing import Any

import numpy as np
import sounddevice as sd

from agents import function_tool
from agents.realtime import (
    RealtimeAgent,
    RealtimePlaybackTracker,
    RealtimeRunner,
    RealtimeSession,
    RealtimeSessionEvent,
)
from agents.realtime.model import RealtimeModelConfig

from scipy.signal import resample_poly


# 尝试导入 dotenv，如果失败则忽略
try:
    from dotenv import load_dotenv
    # 加载当前目录下的 .env 文件
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    print(f"尝试加载 .env 文件: {env_path}")
except ImportError:
    # 如果没有安装 python-dotenv，则跳过
    print("python-dotenv 未安装，跳过 .env 文件加载")
    pass

# 调试：打印 API 密钥信息
api_key = os.getenv('OPENAI_API_KEY')
print(f"API 密钥状态: {'已设置' if api_key else '未设置'}")
if api_key:
    print(f"API 密钥长度: {len(api_key)}")
    print(f"API 密钥前缀: {api_key[:10]}..." if len(api_key) > 10 else f"API 密钥: {api_key}")
else:
    print("警告: OPENAI_API_KEY 环境变量未设置")

# Audio configuration
CHUNK_LENGTH_S = 0.04  # 40ms aligns with realtime defaults
# SAMPLE_RATE = 24000
SAMPLE_RATE = 48000
FORMAT = np.int16
CHANNELS = 1
# ENERGY_THRESHOLD = 0.015  # RMS threshold for barge‑in while assistant is speaking
ENERGY_THRESHOLD = 0.12  # RMS threshold for barge‑in while assistant is speaking

PREBUFFER_CHUNKS = 3  # initial jitter buffer (~120ms with 40ms chunks)
FADE_OUT_MS = 12  # short fade to avoid clicks when interrupting

# Set up logging for OpenAI agents SDK
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
# logger.logger.setLevel(logging.ERROR)


@function_tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."


agent = RealtimeAgent(
    name="Assistant",
    instructions="""
    你始终使用中文回答用户的所有问题。
    如果用户说的内容不是中文，请明确告知：‘我听到的不是中文，请用中文交流’。
    保持语气礼貌自然。
    """,
    # tools=[get_weather],
)


def _truncate_str(s: str, max_length: int) -> str:
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


class NoUIDemo:
    def __init__(self) -> None:
        self.session: RealtimeSession | None = None
        self.audio_stream: sd.InputStream | None = None
        self.audio_player: sd.OutputStream | None = None
        self.recording = False

        # Playback tracker lets the model know our real playback progress
        self.playback_tracker = RealtimePlaybackTracker()

        # Audio output state for callback system
        # Store tuples: (samples_np, item_id, content_index)
        # Use an unbounded queue to avoid drops that sound like skipped words.
        self.output_queue: queue.Queue[Any] = queue.Queue(maxsize=0)
        self.interrupt_event = threading.Event()
        self.current_audio_chunk: tuple[np.ndarray[Any, np.dtype[Any]], str, int] | None = None
        self.chunk_position = 0
        self.bytes_per_sample = np.dtype(FORMAT).itemsize

        # Jitter buffer and fade-out state
        self.prebuffering = True
        self.prebuffer_target_chunks = PREBUFFER_CHUNKS
        self.fading = False
        self.fade_total_samples = 0
        self.fade_done_samples = 0
        self.fade_samples = int(SAMPLE_RATE * (FADE_OUT_MS / 1000.0))

    def _output_callback(self, outdata, frames: int, time, status) -> None:
        """Callback for audio output - handles continuous audio stream from server."""
        if status:
            print(f"Output callback status: {status}")

        # Handle interruption with a short fade-out to prevent clicks.
        if self.interrupt_event.is_set():
            outdata.fill(0)
            if self.current_audio_chunk is None:
                # Nothing to fade, just flush everything and reset.
                while not self.output_queue.empty():
                    try:
                        self.output_queue.get_nowait()
                    except queue.Empty:
                        break
                self.prebuffering = True
                self.interrupt_event.clear()
                return

            # Prepare fade parameters
            if not self.fading:
                self.fading = True
                self.fade_done_samples = 0
                # Remaining samples in the current chunk
                remaining_in_chunk = len(self.current_audio_chunk[0]) - self.chunk_position
                self.fade_total_samples = min(self.fade_samples, max(0, remaining_in_chunk))

            samples, item_id, content_index = self.current_audio_chunk
            samples_filled = 0
            while (
                samples_filled < len(outdata) and self.fade_done_samples < self.fade_total_samples
            ):
                remaining_output = len(outdata) - samples_filled
                remaining_fade = self.fade_total_samples - self.fade_done_samples
                n = min(remaining_output, remaining_fade)

                src = samples[self.chunk_position : self.chunk_position + n].astype(np.float32)
                # Linear ramp from current level down to 0 across remaining fade samples
                idx = np.arange(
                    self.fade_done_samples, self.fade_done_samples + n, dtype=np.float32
                )
                gain = 1.0 - (idx / float(self.fade_total_samples))
                ramped = np.clip(src * gain, -32768.0, 32767.0).astype(np.int16)
                outdata[samples_filled : samples_filled + n, 0] = ramped

                # Optionally report played bytes (ramped) to playback tracker
                try:
                    self.playback_tracker.on_play_bytes(
                        item_id=item_id, item_content_index=content_index, bytes=ramped.tobytes()
                    )
                except Exception:
                    pass

                samples_filled += n
                self.chunk_position += n
                self.fade_done_samples += n

            # If fade completed, flush the remaining audio and reset state
            if self.fade_done_samples >= self.fade_total_samples:
                self.current_audio_chunk = None
                self.chunk_position = 0
                while not self.output_queue.empty():
                    try:
                        self.output_queue.get_nowait()
                    except queue.Empty:
                        break
                self.fading = False
                self.prebuffering = True
                self.interrupt_event.clear()
            return

        # Fill output buffer from queue and current chunk
        outdata.fill(0)  # Start with silence
        samples_filled = 0

        while samples_filled < len(outdata):
            # If we don't have a current chunk, try to get one from queue
            if self.current_audio_chunk is None:
                try:
                    # Respect a small jitter buffer before starting playback
                    if (
                        self.prebuffering
                        and self.output_queue.qsize() < self.prebuffer_target_chunks
                    ):
                        break
                    self.prebuffering = False
                    self.current_audio_chunk = self.output_queue.get_nowait()
                    self.chunk_position = 0
                except queue.Empty:
                    # No more audio data available - this causes choppiness
                    # Uncomment next line to debug underruns:
                    # print(f"Audio underrun: {samples_filled}/{len(outdata)} samples filled")
                    break

            # Copy data from current chunk to output buffer
            remaining_output = len(outdata) - samples_filled
            samples, item_id, content_index = self.current_audio_chunk
            remaining_chunk = len(samples) - self.chunk_position
            samples_to_copy = min(remaining_output, remaining_chunk)

            if samples_to_copy > 0:
                chunk_data = samples[self.chunk_position : self.chunk_position + samples_to_copy]
                # More efficient: direct assignment for mono audio instead of reshape
                outdata[samples_filled : samples_filled + samples_to_copy, 0] = chunk_data
                samples_filled += samples_to_copy
                self.chunk_position += samples_to_copy

                # Inform playback tracker about played bytes
                try:
                    self.playback_tracker.on_play_bytes(
                        item_id=item_id,
                        item_content_index=content_index,
                        bytes=chunk_data.tobytes(),
                    )
                except Exception:
                    pass

                # If we've used up the entire chunk, reset for next iteration
                if self.chunk_position >= len(samples):
                    self.current_audio_chunk = None
                    self.chunk_position = 0

    async def run(self) -> None:
        print("Connecting, may take a few seconds...")

        # Initialize audio player with callback
        chunk_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)
        self.audio_player = sd.OutputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=FORMAT,
            callback=self._output_callback,
            blocksize=chunk_size,  # Match our chunk timing for better alignment
        )
        self.audio_player.start()

        try:
            runner = RealtimeRunner(agent)
            # Attach playback tracker and enable server‑side interruptions + auto response.
            model_config: RealtimeModelConfig = {
                "playback_tracker": self.playback_tracker,
                "initial_model_settings": {
                    "turn_detection": {
                        "type": "semantic_vad",
                        "interrupt_response": True,
                        "create_response": True,
                    },
                },
            }
            async with await runner.run(model_config=model_config) as session:
                self.session = session
                print("Connected. Starting audio recording...")

                # Start audio recording
                await self.start_audio_recording()
                print("Audio recording started. You can start speaking - expect lots of logs!")

                # Process session events
                async for event in session:
                    await self._on_event(event)

        finally:
            # Clean up audio player
            if self.audio_player and self.audio_player.active:
                self.audio_player.stop()
            if self.audio_player:
                self.audio_player.close()

        print("Session ended")

    async def start_audio_recording(self) -> None:
        """Start recording audio from the microphone."""
        print("🎤 正在初始化音频输入流...")
        
        # 检查可用的音频设备
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            print(f"📱 默认输入设备: {default_input}")
            print(f"🎧 可用音频设备数量: {len(devices)}")
        except Exception as e:
            print(f"⚠️  查询音频设备时出错: {e}")
        
        # Set up audio input stream
        try:
            mic_device = 0
            chunk_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)
            self.audio_stream = sd.InputStream(
                device=mic_device,
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                dtype=FORMAT,
                blocksize=chunk_size  # 明确要求一次 40ms
            )
            print(f"✅ 音频流创建成功 - 采样率: {SAMPLE_RATE}Hz, 通道数: {CHANNELS}, 格式: {FORMAT}")
            print(f"✅ 使用音频输入设备: {mic_device} - {sd.query_devices(mic_device)['name']}")
        except Exception as e:
            print(f"❌ 创建音频输入流失败: {e}")
            return

        try:
            self.audio_stream.start()
            self.recording = True
            print("🎵 音频流已启动，开始录制...")
            print(f"📊 音频流状态: active={self.audio_stream.active}")
        except Exception as e:
            print(f"❌ 启动音频流失败: {e}")
            return

        # Start audio capture task
        asyncio.create_task(self.capture_audio())
        print("🔄 音频捕获任务已创建")

    async def capture_audio(self) -> None:
        """Capture audio from the microphone and send to the session."""
        if not self.audio_stream or not self.session:
            print("❌ 音频流或会话未初始化，无法开始音频捕获")
            return

        print("🎯 开始音频捕获循环...")
        # Buffer size in samples
        read_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)
        print(f"📏 读取缓冲区大小: {read_size} 样本 ({CHUNK_LENGTH_S*1000}ms)")

        audio_chunks_sent = 0
        last_energy_log_time = 0

        try:
            # Simple energy-based barge-in: if user speaks while audio is playing, interrupt.
            def rms_energy(samples: np.ndarray[Any, np.dtype[Any]]) -> float:
                if samples.size == 0:
                    return 0.0
                # Normalize int16 to [-1, 1]
                x = samples.astype(np.float32) / 32768.0
                return float(np.sqrt(np.mean(x * x)))

            def downsample_48k_to_24k(samples_48k: np.ndarray) -> np.ndarray:
                """将 48000Hz 音频下采样到 24000Hz 并转换为 int16"""
                import numpy as np
                from scipy.signal import resample_poly

                # 上下采样
                samples_24k = resample_poly(samples_48k, up=1, down=2)

                # 保证幅度不超范围并转换为 int16
                samples_24k = np.clip(samples_24k, -32768, 32767).astype(np.int16)
                return samples_24k

            while self.recording:
                # Check if there's enough data to read
                available = self.audio_stream.read_available

                # print(f"可读取样本: {available}, 目标: {read_size}")
                if available < read_size:
                    await asyncio.sleep(0.01)
                    continue

                # Read audio data
                data, _ = self.audio_stream.read(read_size)
                audio_chunks_sent += 1

                # Convert numpy array to bytes
                # audio_bytes = data.tobytes()

                # 计算音频能量用于调试
                samples = data.reshape(-1)
                current_energy = rms_energy(samples)

                # # 将 48000Hz 音频下采样到 24000Hz
                audio_bytes = downsample_48k_to_24k(samples)
                
                # 每5秒记录一次音频状态
                import time
                current_time = time.time()
                if current_time - last_energy_log_time > 5:
                    print(f"🎙️  音频捕获状态 - 已发送块数: {audio_chunks_sent}, 当前能量: {current_energy:.4f}, 阈值: {ENERGY_THRESHOLD}")
                    last_energy_log_time = current_time

                # Smart barge‑in: if assistant audio is playing, send only if mic has speech.
                assistant_playing = (
                    self.current_audio_chunk is not None or not self.output_queue.empty()
                )
                if assistant_playing:
                    # Compute RMS energy to detect speech while assistant is talking
                    if current_energy >= ENERGY_THRESHOLD:
                        print(f"🔊 检测到用户语音，能量: {current_energy:.4f}，中断助手音频")
                        # Locally flush queued assistant audio for snappier interruption.
                        self.interrupt_event.set()
                        await self.session.send_audio(audio_bytes)
                else:
                    await self.session.send_audio(audio_bytes)

                # Yield control back to event loop
                await asyncio.sleep(0)

        except Exception as e:
            print(f"❌ 音频捕获错误: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
        finally:
            print("🧹 清理音频流资源...")
            if self.audio_stream and self.audio_stream.active:
                self.audio_stream.stop()
                print("⏹️  音频流已停止")
            if self.audio_stream:
                self.audio_stream.close()
                print("🔒 音频流已关闭")

    async def _on_event(self, event: RealtimeSessionEvent) -> None:
        """Handle session events."""
        try:
            if event.type == "agent_start":
                print(f"Agent started: {event.agent.name}")
            elif event.type == "agent_end":
                print(f"Agent ended: {event.agent.name}")
            elif event.type == "handoff":
                print(f"Handoff from {event.from_agent.name} to {event.to_agent.name}")
            elif event.type == "tool_start":
                print(f"Tool started: {event.tool.name}")
            elif event.type == "tool_end":
                print(f"Tool ended: {event.tool.name}; output: {event.output}")
            elif event.type == "audio_end":
                print("Audio ended")
            elif event.type == "audio":
                # Enqueue audio for callback-based playback with metadata
                np_audio = np.frombuffer(event.audio.data, dtype=np.int16)
                # 假设 CHUNK_LENGTH_S = 0.04 s
                n = len(np_audio)
                expected = 24000 * 0.04  # = 960
                print("实际样本数:", n, "与期望:", expected)
                def upsample_24k_to_48k(samples_24k: np.ndarray) -> np.ndarray:
                    # up=2, down=1 => 24k -> 48k
                    return resample_poly(samples_24k, up=2, down=1)

                # 先做 upsample -> 48kHz
                np_audio_48k = upsample_24k_to_48k(np_audio)

                # Non-blocking put; queue is unbounded, so drops won’t occur.
                self.output_queue.put_nowait((np_audio_48k, event.item_id, event.content_index))
            elif event.type == "audio_interrupted":
                print("Audio interrupted")
                # Begin graceful fade + flush in the audio callback and rebuild jitter buffer.
                self.prebuffering = True
                self.interrupt_event.set()
            elif event.type == "error":
                print(f"Error: {event.error}")
            elif event.type == "history_updated":
                pass  # Skip these frequent events
            elif event.type == "history_added":
                pass  # Skip these frequent events
            elif event.type == "raw_model_event":
                print(f"Raw model event: {_truncate_str(str(event.data), 200)}")
            else:
                print(f"Unknown event type: {event.type}")
        except Exception as e:
            print(f"Error processing event: {_truncate_str(str(e), 200)}")


if __name__ == "__main__":
    print("Starting Realtime Agent...")
    demo = NoUIDemo()
    try:
        asyncio.run(demo.run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
