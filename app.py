import streamlit as st
import pandas as pd
import numpy as np
import altair as alt 
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
    
    # Starting HC (Input) - Check for correct f-string closing
    current_inputs[f'{team}_start_hc'] = st.sidebar.number_input(
        f"Starting HC ({team})", min_value=0, value=df_initial.loc[team, 'Starting_HC'], key=f'shc_{team}'
    )
    
    # Monthly Hires (Input) - Check for correct f-string closing
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
            
            current_hc = results_df.loc[prev_month_label, team]
            monthly_hires = inputs[f'{team}_hires']
            monthly_attrition = inputs[f'{team}_attrition']
            quarterly_promotion_rate = inputs[f'{team}_promotion']
            
            # Attrition & New Hires
            attrition_count = current_hc * monthly_attrition
            current_hc = current_hc - attrition_count + monthly_hires
            
            # Promotions
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
        
        # Promotions In
        if m % 3 == 0:
            for team, promo_in_count in promotions_in.items():
                results_df.loc[current_month_label, team] += promo_in_count
                
    
    # Calculate Total Headcount
    results_df['Total Headcount'] = results_df.drop('Start').sum(axis=1)
    
    # Final cleanup: fill NaNs with 0, round to nearest integer, and drop the 'Start' row
    results_df = results_df.fillna(0).round(0).astype(int)
    
    # Create aggregated rows for SMB, CMRL, MM
    df_final = results_df.drop('Start').copy()
    
    df_final['SMB Total'] = df_final[['SMB 1-2 AM', 'SMB 3-4 AM', 'SMB 5-9 AM']].sum(axis=1)
    df_final['CMRL Total'] = df_final[['CMRL 10-19 AM', 'CMRL 20-29 AM', 'CMRL 30-49 AM']].sum(axis=1)
    df_final['MM Total'] = df_final[['MM 50-99 AM', 'MM 100-149 AM']].sum(axis=1)

    return df_final


# Run the model
projection_df = run_forecast(current_inputs, df_initial)

# --- 4. Visualization and Output (Altair Charts with Hover & Highlight) ---

def create_interactive_line_chart(df, teams_to_plot, title):
    # Prepare data for Altair (long format)
    df_long = df[teams_to_plot].reset_index().rename(columns={'index': 'Month'})
    
    # ENSURE 'Month' is correctly formatted as a string for Altair parsing
    df_long['Month'] = df_long['Month'].astype(str)
    
    # Melt the data into long format for Altair
    df_long = pd.melt(df_long, id_vars='Month', var_name='Team', value_name='Headcount')

    # 1. Selection for highlighting (clickable legend)
    selection_highlight = alt.selection_point(
        fields=['Team'],
        bind='legend',
        name='SelectionHighlight'
    )
    
    # 2. Selection for hover/tooltip (for nearest point)
    hover = alt.selection_point(
        fields=['Month'],
        nearest=True,
        on='mouseover',
        empty='none',
        name='HoverSelection'
    )
    
    # Base chart definition
    base = alt.Chart(df_long, title=title).encode(
        # X-axis: Month as a Temporal type (T)
        x=alt.X('Month:T', axis=alt.Axis(title='Month', format="%Y-%m")), 
        # Y-axis: Headcount as a Quantitative type (Q)
        y=alt.Y('Headcount:Q', title='Headcount', axis=alt.Axis(format=',f')),
        color='Team:N', # Color by Team (Nominal type)
        tooltip=['Month:T', 'Team:N', alt.Tooltip('Headcount:Q', format=',f')]
    )

    # Layer 1: Lines (opacity controlled by clickable legend)
    lines = base.mark_line().encode(
        opacity=alt.condition(selection_highlight, alt.value(1), alt.value(0.2))
    )

    # Layer 2: Points (shown on hover, used for tooltips)
    points = lines.mark_point().encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    ).add_params(hover)

    # Layer 3: Rules (vertical line shown on hover)
    rules = base.mark_rule().encode(
        x='Month:T',
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
        tooltip=['Month:T', 'Team:N', alt.Tooltip('Headcount:Q', format=',f')]
    ).add_params(hover)

    # Combine all layers and add the clickable highlight selection
    chart = (lines + rules + points).add_params(
        selection_highlight
    ).properties(
        height=400 
    ).interactive()

    return chart

st.header("Total Headcount Projection")
total_teams = ['Total Headcount', 'SMB Total', 'CMRL Total', 'MM Total']
total_chart = create_interactive_line_chart(projection_df, total_teams, "Aggregate and Total Headcount Forecast")
st.altair_chart(total_chart, use_container_width=True)


st.header("Individual Team Headcount Projections")
individual_chart = create_interactive_line_chart(projection_df, df_initial.index.tolist(), "Individual Team Forecast")
st.altair_chart(individual_chart, use_container_width=True)


st.markdown(f"**Total Projected Headcount by End of 2026:** **{projection_df['Total Headcount'].iloc[-1]:,}**")

st.subheader("Detailed Monthly Projection Table")
st.dataframe(projection_df)