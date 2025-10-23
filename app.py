import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# Set the end date for the forecast
END_DATE = date(2026, 12, 31)

# --- 1. Initial Data Setup (RENAMED TEAMS HERE) ---
# Base data structure reflecting the initial table
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
st.set_page_config(layout="wide", page_title="Headcount Growth Model")

st.title("Interactive Headcount Growth Model 🚀")
st.caption("Adjust the sliders in the sidebar to dynamically forecast team and total headcount through the end of 2026.")

teams = df_initial.index.tolist()
current_inputs = {}

st.sidebar.header("Team Specific Controls")

for team in teams:
    st.sidebar.subheader(f"📊 {team}")
    
    # Starting HC (Input)
    current_inputs[f'{team}_start_hc'] = st.sidebar.number_input(
        f"Starting HC ({team})", min_value=0, value=df_initial.loc[team, 'Starting_HC'], key=f'shc_{team}'
    )

    # Monthly Hires (Input)
    current_inputs[f'{team}_hires'] = st.sidebar.number_input(
        f"Monthly New Hires ({team})", min_value=0, value=df_initial.loc[team, 'Monthly_Hires'], key=f'mhi_{team}'
    )
    
    # Monthly Attrition Rate (%) (Slider)
    current_inputs[f'{team}_attrition'] = st.sidebar.slider(
        f"Monthly Attrition Rate (%) ({team})", 
        min_value=0.0, max_value=10.0, step=0.1, 
        value=df_initial.loc[team, 'Monthly_Attrition_Rate'] * 100,
        format="%.1f %%", key=f'mar_{team}'
    ) / 100.0

    # Quarterly Promotion Rate (%) (Slider)
    current_inputs[f'{team}_promotion'] = st.sidebar.slider(
        f"Quarterly Promotion Rate (%) ({team})", 
        min_value=0.0, max_value=40.0, step=0.5, 
        value=df_initial.loc[team, 'Quarterly_Promotion_Rate'] * 100,
        format="%.1f %%", key=f'qpr_{team}'
    ) / 100.0

# --- 3. Forecasting Logic ---

def run_forecast(inputs, initial_data):
    """Calculates the monthly headcount for each team."""
    
    start_date = date.today()
    
    dates = pd.date_range(start=start_date.replace(day=1), end=END_DATE, freq='M')
    num_months = len(dates)
    
    results_df = pd.DataFrame(
        index=['Start'] + dates.strftime('%Y-%m').tolist(), 
        columns=initial_data.index
    )
    
    for team in initial_data.index:
        results_df.loc['Start', team] = inputs[f'{team}_start_hc']
        
    results_df = results_df.astype(float) 
    
    
    # Simulation loop
    for m in range(1, num_months + 1):
        prev_month_label = results_df.index[m-1]
        current_month_label = dates.strftime('%Y-%m')[m-1]

        results_df.loc[current_month_label] = results_df.loc[prev_month_label]

        promotions_out = {} 
        promotions_in = {} 

        for team in initial_data.index:
            
            # --- Get Inputs for Current Team ---
            current_hc = results_df.loc[prev_month_label, team]
            monthly_hires = inputs[f'{team}_hires']
            monthly_attrition = inputs[f'{team}_attrition']
            quarterly_promotion_rate = inputs[f'{team}_promotion']
            
            # --- 1. Attrition & 2. New Hires ---
            attrition_count = current_hc * monthly_attrition
            current_hc = current_hc - attrition_count + monthly_hires
            
            # --- 3. Promotions (Calculated Monthly, Applied Quarterly) ---
            promotion_destination = initial_data.loc[team, 'Promotion_Destination']
            
            if m % 3 == 0: 
                promoted_count = current_hc * quarterly_promotion_rate
                
                promotions_out[team] = promoted_count
                
                if promotion_destination != 'n/a':
                    promotions_in[promotion_destination] = promotions_in.get(promotion_destination, 0) + promoted_count
                    
                current_hc -= promoted_count
            else:
                promotions_out[team] = 0
                
            results_df.loc[current_month_label, team] = current_hc
        
        # --- 4. Promotions In (Applied only at month m % 3 == 0) ---
        if m % 3 == 0:
            for team, promo_in_count in promotions_in.items():
                results_df.loc[current_month_label, team] += promo_in_count
                
    
    # Calculate Total Headcount
    results_df['Total Headcount'] = results_df.drop('Start').sum(axis=1)
    
    # Final cleanup: fill NaNs with 0, round to nearest integer, and drop the 'Start' row
    results_df = results_df.fillna(0).round(0).astype(int)
    
    # Create aggregated rows for SMB, CMRL, MM (UPDATED TEAM NAMES HERE)
    df_final = results_df.drop('Start').copy()
    
    df_final['SMB Total'] = df_final[['SMB 1-2 AM', 'SMB 3-4 AM', 'SMB 5-9 AM']].sum(axis=1)
    df_final['CMRL Total'] = df_final[['CMRL 10-19 AM', 'CMRL 20-29 AM', 'CMRL 30-49 AM']].sum(axis=1)
    df_final['MM Total'] = df_final[['MM 50-99 AM', 'MM 100-149 AM']].sum(axis=1)

    return df_final


# Run the model
projection_df = run_forecast(current_inputs, df_initial)

# --- 4. Visualization and Output ---

st.header("Total Headcount Projection")
st.line_chart(projection_df[['Total Headcount', 'SMB Total', 'CMRL Total', 'MM Total']])

st.header("Individual Team Headcount Projections")
st.line_chart(projection_df[df_initial.index.tolist()])

st.markdown(f"**Total Projected Headcount by End of 2026:** **{projection_df['Total Headcount'].iloc[-1]:,}**")

st.subheader("Detailed Monthly Projection Table")
st.dataframe(projection_df)