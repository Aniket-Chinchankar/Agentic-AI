import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Image as AgnoImage
from agno.tools.duckduckgo import DuckDuckGoTools
import logging
import tempfile
import os
import traceback
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="💔 Breakup Recovery Squad",
    page_icon="💔",
    layout="wide"
)

# --- AGENT INITIALIZATION ---
def initialize_agents(api_key: str):
    try:
        # FIX 1: Use 'gemini-1.0-pro'. 
        # This is the "Universal" model that works on almost all Free Tier accounts.
        # If this works, you can try changing it to "gemini-1.5-flash" later.
        model_id = "gemini-1.0-pro"
        
        # Initialize the model
        model = Gemini(id=model_id, api_key=api_key)
        
        therapist_agent = Agent(
            model=model,
            name="Therapist Agent",
            instructions=[
                "You are an empathetic therapist. Listen, validate feelings, and offer comfort.",
                "Analyze text for emotional context."
            ],
            markdown=True
        )

        closure_agent = Agent(
            model=model,
            name="Closure Agent",
            instructions=[
                "You are a closure specialist. Create emotional messages and unsent letters.",
                "Focus on emotional release."
            ],
            markdown=True
        )

        routine_planner_agent = Agent(
            model=model,
            name="Routine Planner Agent",
            instructions=[
                "You are a recovery routine planner. Design 7-day challenges and self-care tasks.",
                "Focus on practical steps."
            ],
            markdown=True
        )

        brutal_honesty_agent = Agent(
            model=model,
            name="Brutal Honesty Agent",
            tools=[DuckDuckGoTools()],
            instructions=[
                "You are a direct feedback specialist. Give raw, objective feedback.",
                "Do not sugar-coat."
            ],
            markdown=True
        )
        
        return therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 API Configuration")
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = ""
    
    # Simple text input for the key
    api_key = st.text_input("Gemini API Key", value=st.session_state.api_key_input, type="password")
    
    if api_key:
        st.session_state.api_key_input = api_key
        st.success("Key Saved! ✅")

# --- MAIN UI ---
st.title("💔 Breakup Recovery Squad")

col1, col2 = st.columns(2)
with col1:
    user_input = st.text_area("How are you feeling?", height=150)
with col2:
    uploaded_files = st.file_uploader("Upload chat screenshots", accept_multiple_files=True)

# --- PROCESS LOGIC ---
if st.button("Get Recovery Plan 💝", type="primary"):
    if not st.session_state.api_key_input:
        st.warning("Please enter your API Key in the sidebar!")
    else:
        agents = initialize_agents(st.session_state.api_key_input)
        if all(agents):
            therapist, closure, routine, honesty = agents
            
            try:
                # Process Images (Only if using a model that supports vision, 1.0-pro often doesn't on free tier)
                # We will only pass images if they exist, but be warned 1.0-pro might reject them.
                all_images = []
                if uploaded_files:
                    for file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.name}") as f:
                            f.write(file.getvalue())
                            all_images.append(AgnoImage(filepath=f.name))

                with st.spinner("Analyzing... (Slowed down to prevent crashing)"):
                    st.header("Results")
                    
                    # 1. Therapist
                    st.subheader("🤗 Emotional Support")
                    # Note: We remove images here for 1.0-pro safety. 
                    # If you really need images, we must switch back to 1.5-flash
                    resp = therapist.run(f"User feeling: {user_input}")
                    st.markdown(resp.content)
                    
                    # FIX 2: Rate Limit Pause
                    time.sleep(2) 

                    # 2. Closure
                    st.subheader("✍️ Closure")
                    resp = closure.run(f"Draft closure letter for: {user_input}")
                    st.markdown(resp.content)
                    
                    time.sleep(2)

                    # 3. Routine
                    st.subheader("📅 Plan")
                    resp = routine.run(f"Create routine for: {user_input}")
                    st.markdown(resp.content)
                    
                    time.sleep(2)

                    # 4. Honesty
                    st.subheader("💪 Honest Take")
                    resp = honesty.run(f"Give brutal feedback on: {user_input}") 
                    st.markdown(resp.content)

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.code(traceback.format_exc())