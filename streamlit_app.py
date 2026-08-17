import streamlit as st
import requests
import json
import time

# ============================================================
# ⚠️ CRITICAL SECURITY WARNING – THESE KEYS ARE EXPOSED!
# Go to Google AI Studio and Fish Audio Dashboard RIGHT NOW,
# revoke these keys, and generate new ones.
# Replace the strings below with your NEW keys.
# ============================================================

GEMINI_API_KEY = "AIzaSyDmBDe4mZ8YTtNpLXq8nIMHge2X2Ew8z3g"   # <-- REPLACE
FISH_API_KEY   = "sk-fish-FnUQ4oBOoBfq2KpaRzoxnBmlQ-4dG5PAoEisI774uv0"  # <-- REPLACE
FISH_VOICE_ID  = "YOUR_VOICE_ID"  # Get a real voice ID from Fish Audio library

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
st.markdown("Type something below, and Alex will reply with both wisdom and warmth.")

# Sidebar with donation link
st.sidebar.markdown("## ☕ Support this project")
st.sidebar.markdown("[Buy me a coffee](https://www.buymeacoffee.com)")

# Input area
user_input = st.text_area("💬 What's on your mind?", height=100)
generate = st.button("Generate", type="primary")

if generate and user_input:
    with st.spinner("Alex is thinking..."):
        try:
            # ---------- Step 1: Call Gemini Flash ----------
            gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
            headers_gemini = {
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            }
            # Combine system prompt + user input
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser says: {user_input}"
            payload_gemini = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            
            gemini_resp = requests.post(gemini_url, json=payload_gemini, headers=headers_gemini)
            gemini_resp.raise_for_status()
            gemini_data = gemini_resp.json()
            ai_reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # ---------- Step 2: Convert reply to speech via Fish Audio ----------
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
            
            # Save MP3 to a temporary file (Streamlit handles it)
            with open("output.mp3", "wb") as f:
                f.write(fish_resp.content)
            
            # ---------- Step 3: Display results ----------
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
    if generate and not user_input:
        st.warning("Please type a message first.")

# Footer
st.caption("Powered by Google Gemini Flash & Fish Audio S2.1 Pro Free")
