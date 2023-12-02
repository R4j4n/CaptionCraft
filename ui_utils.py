import os
import streamlit as st

import pandas as pd


# Function to save the uploaded file
def save_uploaded_file(directory, file):
    if not os.path.exists(directory):
        os.makedirs(directory)

    save_pth = os.path.join(directory, file.name)
    with open(os.path.join(directory, file.name), "wb") as f:
        f.write(file.getbuffer())
    return save_pth


def first_occurrence(df, speaker):
    # Filter the DataFrame for the specified speaker
    speaker_data = df[df["Speaker"] == speaker]

    # Check if there's any data for the speaker
    if not speaker_data.empty:
        # Get the first occurrence
        first_row = speaker_data.iloc[0]
        return f"{first_row['Start']} --> {first_row['End']}"
    else:
        return "Speaker not found"
