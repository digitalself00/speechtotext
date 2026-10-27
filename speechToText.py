import os
import tempfile
import streamlit as st
from openai import OpenAI

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="OpenAI Speech-to-Text Tester",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ OpenAI Speech-to-Text Tester")
st.write("Upload an audio file and convert speech into text.")

# --------------------------------------------------
# API configuration
# --------------------------------------------------
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error(
        "OPENAI_API_KEY is not set. "
        "Set your API key in the terminal and restart the app."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------------------------------------
# Model selection
# --------------------------------------------------
model = st.selectbox(
    "Select transcription model",
    [
        "gpt-4o-mini-transcribe",
        "gpt-4o-transcribe",
        "whisper-1"
    ],
    index=0
)

# --------------------------------------------------
# Audio upload
# --------------------------------------------------
audio_file = st.file_uploader(
    "Upload your audio file",
    type=["mp3", "mp4", "mpeg", "mpga", "m4a",
          "wav", "webm", "ogg", "flac"]
)

if audio_file:
    st.success(f"Uploaded: {audio_file.name}")

    # Preview the audio
    st.audio(audio_file)

    # --------------------------------------------------
    # Transcription
    # --------------------------------------------------
    if st.button("🚀 Transcribe Audio", type="primary"):

        try:
            with st.spinner("Transcribing audio with OpenAI..."):

                # Preserve the uploaded file's extension.
                suffix = os.path.splitext(audio_file.name)[1]

                # Create a temporary file for the SDK.
                with tempfile.NamedTemporaryFile(
                    suffix=suffix,
                    delete=False
                ) as temp_file:
                    temp_file.write(audio_file.getvalue())
                    temp_path = temp_file.name

                try:
                    with open(temp_path, "rb") as audio:
                        response = client.audio.transcriptions.create(
                            model=model,
                            file=audio
                        )

                    transcription = response.text

                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            st.success("Transcription completed successfully!")

            st.subheader("📝 Transcribed Text")

            st.text_area(
                "Recognized speech",
                value=transcription,
                height=250
            )

            st.download_button(
                label="⬇️ Download Transcription",
                data=transcription,
                file_name="transcription.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Transcription failed: {e}")

st.divider()

st.caption(
    "Powered by the OpenAI Audio Transcriptions API"
)
