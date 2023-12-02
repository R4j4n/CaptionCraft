import os
import uuid
import time
import pandas as pd
import streamlit as st
from pathlib import Path

from src.config import cfg

from captioncraft import Pipe
from ui_utils import save_uploaded_file, first_occurrence


st.set_page_config(layout="wide")
st.markdown(
    """<h3 style='text-align: Center;'>
    <span style='color: #FF6B6B;'>Caption</span>
    <span style='color: #93C572;'>Craft</span>
</h3>""",
    unsafe_allow_html=True,
)

input_columns, video_column = st.columns([1, 1])


############ Session States #########
if not "path" in st.session_state:
    st.session_state.path = None

if not "source_langauge" in st.session_state:
    st.session_state.source_langauge = None

if not "destination_language" in st.session_state:
    st.session_state.destination_language = None

if not "status" in st.session_state:
    st.session_state.status = False

if not "burn_status" in st.session_state:
    st.session_state.burn_status = False

if not "srt_pth" in st.session_state:
    st.session_state.srt_pth = None

if not "speaker_mapp" in st.session_state:
    st.session_state.speaker_mapp = {}

if not "pipe_object" in st.session_state:
    st.session_state.pipe_object = Pipe()

##################################

with input_columns:
    fileupload, youtube_url_container = st.columns([1, 1])

    with fileupload:
        uploaded_file = st.file_uploader(
            "Choose a video file", type=["mp4", "avi", "mov"]
        )

        if uploaded_file:
            file_contents = uploaded_file.read()

            st.session_state.path = save_uploaded_file(
                os.path.join(cfg.ui.uploaded_save_pth, str(uuid.uuid4())), uploaded_file
            )

        st.session_state.source_langauge = st.selectbox(
            "Video Language",
            st.session_state.pipe_object.get_transcribe_languages(),
            placeholder="english",
        )
    with youtube_url_container:
        st.session_state.path = st.text_area("Youtube URL", height=50, value="")
        st.session_state.destination_language = st.selectbox(
            "SRT language",
            st.session_state.pipe_object.get_translate_languages(),
            index=None,
        )

    if st.button("Start"):
        st.session_state.status = False
        if st.session_state.path == None or st.session_state.path == "":
            st.error("Please provde the URL")

        else:
            with st.spinner(text="This will take some time. Please wait."):
                st.session_state.status = st.session_state.pipe_object(
                    path=st.session_state.path,
                    source_language=st.session_state.source_langauge,
                    destination_language=st.session_state.destination_language,
                )


with video_column:
    if st.session_state.status:
        st.session_state.srt_pth = st.session_state.pipe_object.df_pth
        df = pd.read_csv(st.session_state.srt_pth)
        speakers = set(df["Speaker"].to_list())

        st.session_state.speaker_mapp = {}

        with st.form("my_form", clear_on_submit=False):
            for speaker in speakers:
                occurence = first_occurrence(df, speaker)
                replacement = st.text_input(
                    f"Enter new name for {speaker}: First occurence : {occurence}",
                    key=speaker,
                )
                if replacement:
                    st.session_state.speaker_mapp[speaker] = replacement

            if st.form_submit_button("Burn"):
                st.session_state.pipe_object.remap_speakers(
                    mapp=st.session_state.speaker_mapp
                )
                with st.spinner("Burning 🔥🔥🔥"):
                    st.session_state.burn_status = (
                        st.session_state.pipe_object.burn_subtitle_to_video()
                    )


if st.session_state.burn_status:
    st.video(
        data=str(Path(st.session_state.pipe_object.video_dir).joinpath("subtitled.mp4"))
    )
