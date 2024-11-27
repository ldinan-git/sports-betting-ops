def calculate_implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# Define a function to convert American odds to decimal odds
def american_to_decimal(odds):
    if odds > 0:
        return odds / 100 + 1
    else:
        return 100 / abs(odds) + 1
    
def prob_to_decimal(prob):
    return 1 / prob
    
# Define a function to calculate implied probability
def calculate_implied_probability(decimal_odds):
    return 1 / decimal_odds

# Define a function to calculate projected odds
def calculate_projected_odds(actual_odds, implied_probability):
    return (actual_odds * (1 - implied_probability)) / (1 - (implied_probability * (1 - (actual_odds / (actual_odds + 100)))))

def calculate_ev(true_prob, decimal_odds):
    return (true_prob * decimal_odds) - (1 - true_prob)
