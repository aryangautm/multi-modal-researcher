import wave
from io import BytesIO


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Save PCM data to a wave file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def create_wav_in_memory(pcm, channels=1, rate=24000, sample_width=2) -> bytes:
    """
    Creates a valid WAV file in an in-memory buffer.

    Args:
        audio_data: The raw audio data from the TTS engine.

    Returns:
        The full byte content of a valid .wav file.
    """
    buffer = BytesIO()

    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

    wav_bytes = buffer.getvalue()
    print(type(wav_bytes))
    return wav_bytes


def create_podcast_name(topic):
    """Create a podcast name based on the topic"""
    safe_topic = "".join(
        c for c in topic if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    return f"research_podcast_{safe_topic.replace(' ', '_')}.wav"
