def decide_action(risk_score):
    if risk_score <= 25:
        action = "monitor"
    elif risk_score <= 50:
        action = "rotate"
    elif risk_score <= 75:
        action = "restrict"
    else:
        action = "revoke"

    return {"action": action}
