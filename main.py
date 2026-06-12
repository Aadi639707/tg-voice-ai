import os
import asyncio
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from faster_whisper import WhisperModel
from groq import AsyncGroq
import edge_tts
from config import API_ID, API_HASH, SESSION_STRING, GROQ_API_KEY, COMMAND_PREFIX

app = Client("vc_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(app)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

print("Loading AI Ear Model...")
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

@app.on_message(filters.command("start", prefixes=COMMAND_PREFIX) & filters.me)
async def start(client, message):
    await message.edit_text("✅ Superfast VC AI Bot is ready and active!")

@app.on_message(filters.command("joinvc", prefixes=COMMAND_PREFIX) & filters.me)
async def join_vc(client, message):
    chat_id = message.chat.id
    try:
        await call_py.play(chat_id, MediaStream("silence.mp3"))
        await message.edit_text("✅ Joined VC successfully! I am listening now...")
    except Exception as e:
        await message.edit_text(f"❌ Error: {e}")

@app.on_message(filters.command("leavevc", prefixes=COMMAND_PREFIX) & filters.me)
async def leave_vc(client, message):
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.edit_text("✅ Left VC successfully!")
    except Exception as e:
        await message.edit_text(f"❌ Error: {e}")

async def main():
    if not os.path.exists("silence.mp3"):
        os.system("ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 10 -q:a 9 -acodec libmp3lame silence.mp3 -y")
    print("Bot is starting...")
    await app.start()
    await call_py.start()
    print("✅ Bot is fully active! Go to any group and type .joinvc")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
    
