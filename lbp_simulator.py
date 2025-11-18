
import pandas as pd
import numpy as np

def get_spot_price(token_a_balance, token_b_balance, token_a_weight, token_b_weight):
    """Calculates the pool's market price (spot price)."""
    if token_a_balance == 0 or token_b_balance == 0 or token_a_weight == 0 or token_b_weight == 0:
        return 0
    
    return (token_b_balance / token_b_weight) / (token_a_balance / token_a_weight)

def calculate_token_a_bought(demand_token_b, token_a_balance, token_b_balance, token_a_weight, token_b_weight):
    """
Calculates how much of Token A is bought for a given amount of Token B (e.g., USDC).
    """
    price = get_spot_price(token_a_balance, token_b_balance, token_a_weight, token_b_weight)
    if price == 0:
        return 0
    
    token_a_bought = demand_token_b / price 
    return token_a_bought

def run_simulation(params):
    """Runs the LBP simulation hour by hour."""
    
    hours = params['duration_hours']
    token_a_balance = params['initial_token_a']
    token_b_balance = params['initial_token_b']
    
    weights = np.linspace(params['start_weight'], params['end_weight'], hours + 1)
    
    data = [] 

    for i in range(hours + 1): 
        token_a_weight = weights[i]
        token_b_weight = 1.0 - token_a_weight
        
        current_price = get_spot_price(token_a_balance, token_b_balance, token_a_weight, token_b_weight)
        
        token_a_sold_this_hour = 0
        token_b_gained_this_hour = 0

        if i > 0:
            
            demand_token_b_this_hour = 0
            if current_price <= params['max_price']:
                demand_token_b_this_hour = params['demand_per_hour_token_b']
            
            token_a_sold_this_hour = calculate_token_a_bought(
                demand_token_b_this_hour, token_a_balance, token_b_balance, token_a_weight, token_b_weight
            )
            token_b_gained_this_hour = demand_token_b_this_hour
        
        data.append({
            'hour': i,
            'price': current_price,
            'token_a_balance': token_a_balance,
            'token_b_balance': token_b_balance,
            'token_a_weight': token_a_weight,
            'token_a_sold': token_a_sold_this_hour,
            'token_b_gained': token_b_gained_this_hour,
        })
        
        token_a_balance -= token_a_sold_this_hour
        token_b_balance += token_b_gained_this_hour

    results_df = pd.DataFrame(data)
    
    results_df['proceeds_cumulative_token_b'] = results_df['token_b_gained'].cumsum()

    return results_df