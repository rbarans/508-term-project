import streamlit as st
import requests
import os

# -------------------------
# CONFIG
# -------------------------
ENDPOINT_URL = "https://dbc-b6951fe2-dfb1.cloud.databricks.com/serving-endpoints/tem-project_rana/invocations"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

st.set_page_config(page_title="Suns' Game Predictor", layout="centered")


# -------------------------
# CUSTOM FONTS + COLORS
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Bebas+Neue&display=swap" rel="stylesheet">

<style>

body {
    background-color: #000000;
}

.header-container {
    position: relative;
    width: 100%;
}

.header-image {
    width: 100%;
    height: 380px;
    object-fit: cover;
    border-bottom: 3px solid #362B4D;
}

.header-title {
    position: absolute;
    top: 45%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Anton', sans-serif;
    font-size: 70px;
    color: white;
    letter-spacing: 4px;
    text-shadow: 4px 4px 10px #000;
}

.stApp {
    background-color: #000000;
}

.main-card {
    background-color: #0d0d0d;
    border: 4px solid #362B4D !important;
    box-shadow: 0 0 25px #5C2E52;
    padding: 25px;
    border-radius: 12px;
}

label, .stSelectbox label, .stNumberInput label {
    font-family: 'Anton', sans-serif;
    font-size: 22px !important;
    color: #F0B940 !important;
}

.sublabel {
    font-size: 14px;
    font-family: Arial, sans-serif;
    color: #cccccc;
    opacity: 0.75;
    margin-top: -8px;
}

.stNumberInput > div > div,
.stSelectbox > div > div,
.stTextInput > div > div > input {
    border: 3px solid #7D344F !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

.stButton > button {
    background-image: url('https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg');
    background-size: cover;
    background-position: center 40%;
    border: 3px solid #C34023;
    color: white;
    font-family: 'Anton', sans-serif;
    font-size: 26px;
    padding: 12px 20px;
    width: 50%;
    margin-left: 25%;
    text-shadow: 2px 2px 5px #000;
}

.stButton > button:hover {
    transform: scale(1.04);
}

</style>
""", unsafe_allow_html=True)


# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div class="header-container">
    <img class="header-image" src="https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg">
    <div class="header-title">PHOENIX SUNS</div>
</div>
""", unsafe_allow_html=True)


# -------------------------
# EXPLANATION LOGIC
# -------------------------
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
        explanation.append("The opponent has a small losing streak, slightly helping the Suns.")

    if ss >= 2:
        explanation.append(f"The Suns are on a +{ss} win streak contributing positively.")
    elif ss == 1:
        explanation.append("The Suns enter with mild positive momentum (+1).")
    elif ss <= -1:
        explanation.append(f"The Suns have a losing streak ({ss}), pulling prediction downward.")

    rest_diff = sr - orr
    if sr >= 3:
        explanation.append(f"The Suns have {sr} days of rest; historically 3+ days correlates with lower win probability.")
    elif rest_diff > 0:
        explanation.append(f"The Suns have a slight rest advantage ({sr} vs {orr}).")
    elif rest_diff == 0:
        explanation.append("Both teams have equal rest.")
    else:
        explanation.append(f"The opponent has more rest ({orr} vs {sr}), reducing Suns’ chances.")

    if loc == "Home":
        explanation.append("Playing at home provides a small benefit.")
    else:
        explanation.append("Playing away slightly lowers Suns win probability.")

    # Clean WIN explanation
    if prob >= 0.5:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(word in line.lower() for word in ["loss", "losing", "lower", "reduces"]):
                continue
            cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors modestly support the Suns in this matchup.")
        explanation = cleaned

    else:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(word in line.lower() for word in ["loss", "losing", "reduces", "lower"]):
                cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors tilt the prediction slightly toward a loss.")
        explanation = cleaned

    return explanation


# -------------------------
# MAIN CARD
# -------------------------
with st.container():
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)

    st.subheader("Game Inputs")

    col1, col2 = st.columns(2)

    with col1:
        location = st.selectbox("Location", ["Home", "Away"])

        suns_streak = st.number_input("Suns' Streak", step=1)
        st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)

        suns_rest = st.number_input("Suns’ Rest Days", min_value=1, step=1)

    with col2:
        opponent = st.selectbox("Opponent", [
            "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW",
            "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK",
            "OKC","ORL","PHI","POR","SAC","SAS","TOR","UTA","WAS"
        ])

        opp_streak = st.number_input("Opponent Streak", step=1)
        st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)

        opp_rest = st.number_input("Opponent Rest Days", min_value=1, step=1)

    predict = st.button("PREDICT")

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# MODEL CALL
# -------------------------
if predict:
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
        r = requests.post(
            ENDPOINT_URL,
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload
        )
        prob = r.json()["predictions"][0]

    prediction = "WIN" if prob >= 0.5 else "LOSS"
    color = "#f3d221" if prediction == "WIN" else "#e0357f"

    st.markdown(f"""
        <h3 style='color:{color}; font-family:Anton;'>
            Suns {prediction}!
        </h3>
        <div style='color:white; font-family:Bebas Neue; font-size:20px;'>
            Win Probability: {prob:.3f}
        </div>
    """, unsafe_allow_html=True)

    explanation = generate_explanation(payload["dataframe_records"][0], prob)

    st.subheader("Why This Prediction?")
    for line in explanation:
        st.markdown(f"- {line}")