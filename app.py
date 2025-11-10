import streamlit as st
import pandas as pd
import lbp_simulator 

COMMON_TOKENS = ["TKN", "USDC", "DAI", "USDT", "WETH", "WBTC", "Custom..."]


st.set_page_config(
    page_title="LBP Simulator",  
    page_icon="images/balancer.png", 
    layout="wide"
)

st.title("LBP Simulator")


st.sidebar.image("images/balancer.png", width=100)
st.sidebar.title("Simulation Setup")
st.sidebar.markdown("---")

with st.sidebar.container(border=True):
    st.subheader("Step 1: Project & Tokens")
    
    col1, col2 = st.columns(2)
    token_a_selection = st.selectbox(
        "Sale Token", 
        options=COMMON_TOKENS, 
        index=COMMON_TOKENS.index("TKN")
    )
    if token_a_selection == "Custom...":
        token_a_name = col1.text_input("Custom Sale Token Symbol", "MY_TKN")
    else:
        token_a_name = token_a_selection

    token_b_selection = st.selectbox(
        "Collateral Token", 
        options=COMMON_TOKENS, 
        index=COMMON_TOKENS.index("USDC")
    )
    if token_b_selection == "Custom...":
        token_b_name = col2.text_input("Custom Collateral Symbol", "MY_USD")
    else:
        token_b_name = token_b_selection

    total_supply = st.number_input(f"Total Supply ({token_a_name})", 
                                   value=1_000_000_000, 
                                   step=1_000_000, 
                                   format="%d",
                                   help=f"The total supply of {token_a_name}, used for FDV calculation.")


with st.sidebar.container(border=True):
    st.subheader("Step 2: Pool Parameters")
    
    initial_token_a = st.number_input(f"Initial {token_a_name} (In Pool)", 
                                      value=7500000, 
                                      step=100000,
                                      help="Amount of tokens you will deposit into the pool to sell.")
    
    col1, col2 = st.columns(2)
    start_weight = st.slider(f"Start {token_a_name} (%)", 50, 99, 99, help="Initial TKN weight. High (e.g., 98%) to create high sell pressure.")
    end_weight = st.slider(f"End {token_a_name} (%)", 1, 50, 30, help="Final TKN weight.")
    
    duration_days = st.slider("Duration (Days)", 1, 7, 3, help="Total duration of the LBP.")


with st.sidebar.container(border=True):
    st.subheader("Step 3: Set Initial Price")
    
    calc_from_fdv = st.toggle(f"Calculate Initial {token_b_name} via FDV?", 
                            value=True, 
                            help="Toggle on to calculate the required collateral deposit based on your target FDV.")

    if calc_from_fdv:
        initial_fdv = st.number_input(f"Desired Initial FDV ($)", 
                                      value=100_000_000, 
                                      step=1_000_000, 
                                      format="%d")
        
        if total_supply > 0 and start_weight < 100:
            target_price = initial_fdv / total_supply
            weight_a = start_weight / 100.0
            weight_b = 1.0 - weight_a
            
            initial_token_b = target_price * (initial_token_a / weight_a) * weight_b
            
            st.metric(f"Required {token_b_name} Deposit", f"${initial_token_b:,.2f}")
            st.caption(f"To achieve a start price of ${target_price:,.4f}")
        else:
            initial_token_b = 0
            st.error("Total Supply must be > 0 and Start Weight < 100.")

    else:
        initial_token_b = st.number_input(f"Manual {token_b_name} Deposit", 
                                          value=1333333.0, 
                                          step=10000.0, 
                                          format="%.2f")

with st.sidebar.expander("Step 4: Demand Model (Advanced)"):
    max_price = st.number_input(f"Max. Buy Price ({token_b_name})", 
                                value=15.0, 
                                step=0.5, 
                                format="%.2f",
                                help="The price ceiling the market is willing to pay. Above this, demand goes to zero.")
    demand_per_hour_token_b = st.number_input(f"Demand ({token_b_name}/Hour)", 
                                              value=400000.0, 
                                              step=10000.0, 
                                              format="%.2f",
                                              help="How much capital (in collateral) the market is willing to spend per hour, if the price is below the ceiling.")

st.sidebar.markdown("---")
run_button = st.sidebar.button("Run Simulation", type="primary")

if run_button:

    params = {
        'initial_token_a': initial_token_a,
        'initial_token_b': initial_token_b, 
        'start_weight': start_weight / 100.0, 
        'end_weight': end_weight / 100.0,   
        'duration_hours': duration_days * 24,
        'max_price': max_price,
        'demand_per_hour_token_b': demand_per_hour_token_b
    }

    results_df = lbp_simulator.run_simulation(params)

    st.header("Simulation Results")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Key Metrics & Proceeds", 
        "Price & Demand", 
        "Pool Balances", 
        "Raw Data"
    ])

    with tab1:
        total_proceeds = results_df['proceeds_cumulative_token_b'].iloc[-1]
        final_price = results_df['price'].iloc[-1]
        tokens_sold = params['initial_token_a'] - results_df['token_a_balance'].iloc[-1]
        avg_price = total_proceeds / tokens_sold if tokens_sold > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"Total Proceeds ({token_b_name})", f"${total_proceeds:,.2f}")
        col2.metric(f"Tokens Sold ({token_a_name})", f"{tokens_sold:,.0f}")
        col3.metric(f"Avg. Sale Price ({token_b_name})", f"${avg_price:,.3f}")
        col4.metric(f"Final Price ({token_b_name})", f"${final_price:,.3f}")

        st.subheader(f"Cumulative Proceeds ({token_b_name})")

        plot_df_proceeds = results_df.set_index('hour').rename(
            columns={'proceeds_cumulative_token_b': f"Cumulative Proceeds ({token_b_name})"}
        )
        st.area_chart(plot_df_proceeds[f"Cumulative Proceeds ({token_b_name})"])

    with tab2:
        st.subheader(f"Price Curve ({token_b_name})")
        
        plot_df_price = results_df.set_index('hour').rename(
            columns={'price': f"Price ({token_b_name})"}
        )
        st.line_chart(plot_df_price[f"Price ({token_b_name})"])
        
        
        st.subheader(f"Hourly Demand ({token_a_name})")
        
        plot_df_demand = results_df.set_index('hour').rename(
            columns={'token_a_sold': f"Hourly Sold ({token_a_name})"}
        )
        st.bar_chart(plot_df_demand[f"Hourly Sold ({token_a_name})"])

    with tab3:
        st.subheader("Pool Balances")

        plot_df_balances = results_df.set_index('hour').rename(columns={
            'token_a_balance': token_a_name,
            'token_b_balance': token_b_name
        })
        st.line_chart(plot_df_balances[[token_a_name, token_b_name]])

    with tab4:
        st.subheader("Raw Simulation Data")

        rename_map = {
            'hour': 'Hour',
            'token_a_balance': f"{token_a_name} Balance",
            'token_b_balance': f"{token_b_name} Balance",
            'price': f"Price ({token_b_name})",
            'token_a_sold': f"Hourly Sold ({token_a_name})",
            'token_a_weight':f"{token_a_name} Weight",
            'token_b_gained':f"{token_b_name} Gained",
            'proceeds_cumulative_token_b': f"Cumulative Proceeds ({token_b_name})",
            'weight_a': f"{token_a_name} Weight", 
            'weight_b': f"{token_b_name} Weight" 
        }
        
        
        display_df = results_df.rename(columns={
            k: v for k, v in rename_map.items() if k in results_df.columns
        })
        
        st.dataframe(display_df.style.format(precision=2), width="stretch")

else:
    st.info("Adjust the parameters in the sidebar and click 'Run Simulation' to start.")