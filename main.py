import os
import asyncio
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from faster_whisper import WhisperModel
from groq import AsyncGroq
import edge_tts
from config import API_ID, API_HASH, SESSION_STRING, GROQ_API_KEY, COMMAND_PREFIX

# 1. Bot and Clients Setup
app = Client("vc_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(app)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# 2. Faster-Whisper Model Load (Superfast Offline STT)
print("Loading AI Ear Model...")
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

# --- Commands ---

@app.on_message(filters.command("start", prefixes=COMMAND_PREFIX) & filters.me)
async def start(client, message):
    await message.edit_text("✅ Superfast VC AI Bot is ready and active!")

@app.on_message(filters.command("joinvc", prefixes=COMMAND_PREFIX) & filters.me)
async def join_vc(client, message):
    chat_id = message.chat.id
    try:
        # A silent audio needs to be played to keep the bot active in VC
        await call_py.join_group_call(chat_id, AudioPiped("silence.mp3"))
        await message.edit_text("✅ Joined VC successfully! I am listening now...")
    except Exception as e:
        await message.edit_text(f"❌ Error: {e}")

@app.on_message(filters.command("leavevc", prefixes=COMMAND_PREFIX) & filters.me)
async def leave_vc(client, message):
    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.edit_text("✅ Left VC successfully!")
    except Exception as e:
        await message.edit_text(f"❌ Error: {e}")

# --- Core AI Logic (Listen -> Think -> Speak) ---
async def process_voice_and_reply(audio_file_path, chat_id):
    try:
        # Step A: Listen (Audio to Text) - ~0.5 seconds
        segments, info = whisper_model.transcribe(audio_file_path, beam_size=5)
        user_text = "".join([segment.text for segment in segments])
        
        if not user_text.strip():
            return
            
        # Step B: Think (Groq AI) - < 1 second
        completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a smart voice assistant operating on a Telegram Voice Chat. Keep your answers short, direct, and conversational."},
                {"role": "user", "content": user_text}
            ],
            model="llama3-8b-8192", # Superfast Groq Model
        )
        ai_reply = completion.choices[0].message.content

        # Step C: Speak (Text to Audio) - < 1 second
        output_audio = "reply.mp3"
        # Using Swara for clear Hindi-English mixed pronunciation
        communicate = edge_tts.Communicate(ai_reply, "hi-IN-SwaraNeural") 
        await communicate.save(output_audio)

        # Step D: Play reply in VC
        await call_py.play(chat_id, AudioPiped(output_audio))
            
    except Exception as e:
        print(f"Processing Error: {e}")

# --- Bot Start Logic ---
async def main():
    # Generating a dummy silence file required for joining VC
    if not os.path.exists("silence.mp3"):
        os.system("ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 10 -q:a 9 -acodec libmp3lame silence.mp3 -y")
    
    print("Bot is starting...")
    await app.start()
    await call_py.start()
    print("✅ Bot is fully active! Go to any group and type .joinvc")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
  
