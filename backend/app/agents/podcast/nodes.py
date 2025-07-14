from app.core.config import Configuration
from app.core.llm import genai_client
from app.prompts.podcast import podcast_base
from google.genai import types
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from .state import PodcastState
from .tools import create_wav_in_memory


def generate_podcast_script(state: PodcastState, config: RunnableConfig) -> dict:
    """Generate the podcast script using the provided topic and texts."""
    configuration = Configuration.from_runnable_config(config)
    script_prompt = PromptTemplate.from_template(podcast_base).invoke(
        {
            "topic": state["topic"],
            "research_text": state.get("research_text", ""),
            "video_text": state.get("video_text", ""),
        }
    )

    script_response = genai_client.models.generate_content(
        model=configuration.synthesis_model,
        contents=script_prompt,
        config={"temperature": configuration.podcast_script_temperature},
    )

    podcast_script = script_response.candidates[0].content.parts[0].text

    return {"podcast_script": podcast_script}


def create_podcast_node(state: PodcastState, config: RunnableConfig) -> dict:
    """Node that creates a render the final podcast discussion"""
    configuration = Configuration.from_runnable_config(config)
    podcast_script = state.get("podcast_script", "")

    tts_prompt = (
        f"TTS the following conversation between Mike and Dr. Sarah:\n{podcast_script}"
    )

    response = genai_client.models.generate_content(
        model=configuration.tts_model,
        contents=tts_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Mike",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=configuration.mike_voice,
                                )
                            ),
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Dr. Sarah",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=configuration.sarah_voice,
                                )
                            ),
                        ),
                    ]
                )
            ),
        ),
    )

    # Step 3: Save audio file
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    audio_bytes = create_wav_in_memory(
        audio_data,
        configuration.tts_channels,
        configuration.tts_rate,
        configuration.tts_sample_width,
    )

    print(f"Podcast saved")

    return {"podcast_script": podcast_script, "podcast_audio_bytes": audio_bytes}
