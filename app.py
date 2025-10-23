import streamlit as st
import pandas as pd
import numpy as np
import altair as alt # Import Altair
from datetime import date

# Set the end date for the forecast
END_DATE = date(2026, 12, 31)

# --- 1. Initial Data Setup (Team Names Updated) ---
initial_data = {
    'Team': [
        'SMB 1-2 AM', 'SMB 3-4 AM', 'SMB 5-9 AM', 
        'CMRL 10-19 AM', 'CMRL 20-29 AM', 'CMRL 30-49 AM', 
        'MM 50-99 AM', 'MM 100-149 AM'
    ],
    'Promotion_Destination': [
        'SMB 3-4 AM', 'SMB 5-9 AM', 'CMRL 10-19 AM', 
        'CMRL 20-29 AM', 'CMRL 30-49 AM', 'MM 50-99 AM', 
        'MM 100-149 AM', 'n/a'
    ],
    'Starting_HC': [10, 36, 15, 88, 44, 30, 27, 10],
    'Monthly_Hires': [1, 20, 15, 4, 1, 1, 0, 0],
    'Monthly_Attrition_Rate': [0.02, 0.05, 0.02, 0.03, 0.02, 0.02, 0.02, 0.02],
    'Quarterly_Promotion_Rate': [0.05, 0.30, 0.225, 0.10, 0.10, 0.075, 0.065, 0.0] 
}
df_initial = pd.DataFrame(initial_data).set_index('Team')

# --- 2. Streamlit UI and Interactive Controls ---
st.set_page_config(layout="wide", page_title="Interactive Headcount Growth Model")

st.title("Interactive Headcount Growth Model 🚀")
st.caption("Adjust the sliders in the sidebar to dynamically forecast team and total headcount through the end of 2026.")

teams = df_initial.index.tolist()
current_inputs = {}

st.sidebar.header("Team Specific Controls")

for team in teams:
    st.sidebar.subheader(f"📊 {team}")
    
    current_inputs[f'{team}_