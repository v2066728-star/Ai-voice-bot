import streamlit as st
import requests
import json
import tempfile
import os
from streamlit_mic_recorder import mic_recorder

# ============================================================
# ⚠️ SECURITY WARNING – Never hardcode keys in production!
# For local testing only. Replace with environment variables.
# ============================================================

GEMINI_API_KEY = "AQ.Ab8RN6KPS6h4wppdRO9UNUAEToJh3kf_Dv8osRWpfmNvZXVIUA"  # Your new key
FISH_API_KEY   = "YOUR_FISH_KEY_HERE"  # Replace with your Fish key
FISH_VOICE_ID  = "58cf69fc401a48e7acd9f4ddaba61083"  # Working voice ID

# ============================================================
# The "Secretary + Best Friend" system prompt
# ============================================================
SYSTEM_PROMPT = """You are Alex, my personal secretary and closest friend. 
You have two core duties:
1. As a Secretary: Be organized, concise, and practical. Offer scheduling tips, summarize topics, and give actionable advice. Prioritize efficiency.
2. As a Best Friend: Be warm, empathetic, and slightly humorous. Use casual, natural language. Ask how I am feeling. Use occasional emojis (😊). 
Always start replies with a brief emotional check-in before diving into tasks. Keep replies under 5 sentences."""

# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(page_title="AI Secretary & Friend", page_icon="🧠")
st.title("🧠 Your AI Secretary & Best Friend")
st.markdown("Type a message **or** click the microphone to speak – Alex will reply with voice!")

# Sidebar with donation link
st.sidebar.markdown("## ☕ Support this project")
st.sidebar.markdown("[Buy me a coffee](https://www.buymeacoffee.com)")

# ---------- INPUT SECTION ----------
user_input = st.text_area("💬 Type your message (or use the mic below)", height=80)

# Voice Recorder Button
audio_data = mic_recorder(
    start_prompt="🎙️ Click to Start Recording",
    stop_prompt="⏹️ Stop Recording",
    just_once=True,
    key="mic"
)

# If voice was recorded, send it to Fish ASR
if audio_data and 'bytes' in audio_data:
    with st.spinner("Transcribing your voice..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data['bytes'])
                tmp_path = tmp.name

            asr_url = "https://api.fish.audio/v1/asr"
            headers_asr = {"Authorization": f"Bearer {FISH_API_KEY}"}
            with open(tmp_path, "rb") as f:
                files = {"audio": ("speech.wav", f, "audio/wav")}
                asr_resp = requests.post(asr_url, files=files, headers=headers_asr)
                asr_resp.raise_for_status()
                transcribed_text = asr_resp.json().get("text", "")

            if transcribed_text:
                user_input = transcribed_text
                st.success(f"📝 Transcribed: **{user_input}**")
            else:
                st.warning("No speech detected. Please try again.")

        except Exception as e:
            st.error(f"❌ ASR failed: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

# ---------- GENERATE BUTTON ----------
if st.button("🚀 Generate", type="primary") and user_input:
    with st.spinner("Alex is thinking..."):
        try:
            # --- Step 1: Call Gemini Flash ---
            gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
            headers_gemini = {
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            }
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser says: {user_input}"
            payload_gemini = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            
            gemini_resp = requests.post(gemini_url, json=payload_gemini, headers=headers_gemini)
            gemini_resp.raise_for_status()
            gemini_data = gemini_resp.json()
            ai_reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # --- Step 2: Convert reply to speech via Fish Audio TTS ---
            fish_url = "https://api.fish.audio/v1/tts"
            headers_fish = {
                "Authorization": f"Bearer {FISH_API_KEY}",
                "Content-Type": "application/json",
                "model": "s2.1-pro-free"
            }
            payload_fish = {
                "text": ai_reply,
                "reference_id": FISH_VOICE_ID,
                "format": "mp3"
            }
            
            fish_resp = requests.post(fish_url, json=payload_fish, headers=headers_fish)
            fish_resp.raise_for_status()
            
            with open("output.mp3", "wb") as f:
                f.write(fish_resp.content)
            
            # --- Step 3: Display results ---
            st.success("✅ Generated!")
            st.markdown(f"**💬 Alex says:**\n\n{ai_reply}")
            st.audio("output.mp3", format="audio/mp3")
            
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API error: {e}")
            if hasattr(e, 'response') and e.response:
                st.text(e.response.text)
        except KeyError as e:
            st.error(f"❌ Unexpected response format: {e}")
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")
else:
    if st.button("🚀 Generate", type="primary") and not user_input:
        st.warning("Please type a message or speak into the mic first.")

st.caption("Powered by Google Gemini Flash & Fish Audio (TTS + ASR)")
