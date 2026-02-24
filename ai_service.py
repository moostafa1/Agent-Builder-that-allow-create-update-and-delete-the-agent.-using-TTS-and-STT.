import os
import wave
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

from openai import AsyncOpenAI
from groq import AsyncGroq
from google import genai
from google.genai import types

load_dotenv()

def save_wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Wraps raw PCM audio from Gemini into a playable WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

class AIServiceFactory:
    def __init__(self):
        self.provider = os.getenv("ACTIVE_AI_PROVIDER", "openai").lower()
        
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    @property
    def active_model_name(self) -> str:
        """Returns the exact LLM model string currently being used."""
        if self.provider == "gemini":
            return "gemini-2.5-flash"
        elif self.provider == "groq":
            return "llama-3.3-70b-versatile"
        elif self.provider == "openai":
            return "gpt-4o-mini"
        return "unknown"

    async def generate_chat_response(self, system_prompt: str, chat_history: List[Dict], new_message: str) -> str:
        """LLM Text Generation"""
        if self.provider == "gemini":
            gemini_history = []
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            
            response = await asyncio.to_thread(
                self.gemini_client.models.generate_content,
                model='gemini-2.5-flash',
                contents=gemini_history + [new_message],
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
            return response.text

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": new_message})

        if self.provider == "openai":
            response = await self.openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
            return response.choices[0].message.content
            
        elif self.provider == "groq":
            response = await self.groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            return response.choices[0].message.content
            
        else:
            raise ValueError(f"Unsupported AI Provider: {self.provider}")

    async def transcribe_audio(self, file_path: str) -> str:
        """Speech-to-Text (STT)"""
        if self.provider == "gemini":
            def gemini_stt():
                # Read bytes directly to bypass the slow File Upload API
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
                
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        'Generate an exact transcript of this audio.',
                        types.Part.from_bytes(data=audio_bytes, mime_type='audio/webm')
                    ]
                )
                return response.text
            return await asyncio.to_thread(gemini_stt)
            
        elif self.provider == "groq":
            with open(file_path, "rb") as file:
                # Force tuple format so Groq recognizes the WebM MIME type
                transcription = await self.groq_client.audio.transcriptions.create(
                    file=("audio.webm", file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="json",
                    language="en"
                )
                return transcription.text
                
        elif self.provider == "openai":
            with open(file_path, "rb") as file:
                transcription = await self.openai_client.audio.transcriptions.create(
                    model="gpt-4o-transcribe", 
                    file=file
                )
                return transcription.text

    async def text_to_speech(self, text: str, output_path: str) -> str:
        """Text-to-Speech (TTS)"""
        if self.provider == "gemini":
            def gemini_tts():
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
                            )
                        ),
                    )
                )
                data = response.candidates[0].content.parts[0].inline_data.data
                save_wave_file(output_path, data)
            await asyncio.to_thread(gemini_tts)
            
        elif self.provider == "groq":
            # Use the streaming response pattern to safely handle async binary data
            async with self.groq_client.audio.speech.with_streaming_response.create(
                model="playai-tts",
                voice="Fritz-PlayAI",
                input=text,
                response_format="wav"
            ) as response:
                await response.stream_to_file(output_path)

        elif self.provider == "openai":
            async with self.openai_client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="coral",
                input=text,
            ) as response:
                await response.stream_to_file(output_path)
                
        return output_path

ai_service = AIServiceFactory()