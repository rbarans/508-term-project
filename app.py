import streamlit as st
import requests
import os

ENDPOINT_URL = "https://dbc-b6951fe2-dfb1.cloud.databricks.com/serving-endpoints/tem-project_rana/invocations"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

st.set_page_config(page_title="Suns' Game Predictor", layout="centered")

# -----------------------------
# Header
# -----------------------------
st.title("🏀 Phoenix Suns Game Predictor")
st.caption("Enter game context to generate a model prediction.")

# -----------------------------
# Explanation Logic
# -----------------------------
def generate_explanation(features, prob):
    opp = features["opponent"]
    loc = features["location"]
    ss = features["suns_streak"]
    os_ = features["opp_streak"]
    sr = features["suns_rest"]
    orr = features["opp_rest"]

    explanation = []

    explanation.append(
        "The model predicts a WIN primarily because:" if prob >= 0.5
        else "The model predicts a LOSS because:"
    )

    if os_ >= 3:
        explanation.append(f"The opponent is on a strong positive streak (+{os_}), which historically correlates with Suns losses.")
    elif os_ == 2:
        explanation.append("The opponent has a +2 win streak, offering slight momentum.")
    elif os_ == 1:
        explanation.append("The opponent has a mild +1 winning streak.")
    elif os_ <= -2:
        explanation.append(f"The opponent has been struggling (streak {os_}), which benefits the Suns.")
    elif os_ == -1:
        explanation.append("The opponent has a small losing streak, slightly benefiting the Suns.")

    if ss >= 2:
        explanation.append(f"The Suns have a +{ss} win streak contributing positively.")
    elif ss == 1:
        explanation.append("The Suns enter with mild positive momentum (+1).")
    elif ss <= -1:
        explanation.append(f"The Suns have a losing streak ({ss}), which pushes prediction downward.")

    rest_diff = sr - orr

    if sr >= 3:
        explanation.append(f"The Suns have {sr} days of rest; historically 3+ days correlates with lower win probability.")
    elif rest_diff > 0:
        explanation.append(f"The Suns have a rest advantage ({sr} vs {orr}).")
    elif rest_diff == 0:
        explanation.append("Both teams have equal rest.")
    else:
        explanation.append(f"The opponent has more rest ({orr} vs {sr}), reducing Suns' chances.")

    if loc == "Home":
        explanation.append("Playing at home provides a small benefit.")
    else:
        explanation.append("Playing away slightly lowers Suns win probability.")

    if prob >= 0.5:
        cleaned = [explanation[0]]

        for line in explanation[1:]:
            if any(bad in line.lower() for bad in ["loss", "losing", "reduces", "lower", "pulls", "strong positive streak"]):
                continue

        cleaned.append(line)

        if len(cleaned) == 1:
            cleaned.append("Several factors modestly support the Suns in this matchup.")

        explanation = cleaned
    else:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(bad in line.lower() for bad in ["loss", "losing", "reduces", "lower", "strong positive streak"]):
                cleaned.append(line)

        if len(cleaned) == 1:
            cleaned.append("Several model-learned factors tilt the prediction toward a loss.")

        explanation = cleaned

    return explanation

# -----------------------------
# Form Inputs (Modern Streamlit Layout)
# -----------------------------
with st.form("prediction_form"):
    st.subheader("Game Inputs")

    col1, col2 = st.columns(2)

    with col1:
        location = st.selectbox("Location", ["Home", "Away"])
        opponent = st.selectbox("Opponent", [
            "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW","HOU","IND",
            "LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI","POR",
            "SAC","SAS","TOR","UTA","WAS"
        ])

        suns_streak = st.number_input("Suns' Streak", step=1, format="%d")
        st.caption("Losses represented with (-)")

        suns_rest = st.number_input("Suns’ Rest Days", min_value=1, step=1, format="%d")

    with col2:
        opp_streak = st.number_input("Opponent Streak", step=1, format="%d")
        st.caption("Losses represented with (-)")

        opp_rest = st.number_input("Opponent Rest Days", min_value=1, step=1, format="%d")

    submitted = st.form_submit_button("Predict")

# -----------------------------
# Submit & Call Model
# -----------------------------
if submitted:
    payload = {
        "dataframe_records": [{
            "opponent": opponent,
            "location": location,
            "suns_streak": int(suns_streak),
            "opp_streak": int(opp_streak),
            "suns_rest": int(suns_rest),
            "opp_rest": int(opp_rest),
        }]
    }

    with st.spinner("Contacting model…"):
        try:
            r = requests.post(
                ENDPOINT_URL,
                headers={
                    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload
            )
            db_response = r.json()
            prob = db_response["predictions"][0]

        except Exception as e:
            st.error(f"Model request failed: {e}")
            st.stop()

    prediction = "WIN" if prob >= 0.5 else "LOSS"
    color = "gold" if prediction == "WIN" else "salmon"

    st.success(f"Prediction: **{prediction}**")
    st.write(f"**Win Probability:** `{prob:.3f}`")

    explanation = generate_explanation(payload["dataframe_records"][0], prob)

    st.subheader("Why This Prediction?")
    st.write(explanation[0])
    for line in explanation[1:]:
        st.markdown(f"- {line}")
