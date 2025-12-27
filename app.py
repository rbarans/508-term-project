import streamlit as st
import requests
import os
import json

# -------------------------
# CONFIG
# -------------------------
ENDPOINT_URL = "https://dbc-b6951fe2-dfb1.cloud.databricks.com/serving-endpoints/tem-project_rana/invocations"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

st.set_page_config(page_title="Suns' Game Predictor", layout="centered")

# Token check
if not DATABRICKS_TOKEN:
    st.error("DATABRICKS_TOKEN environment variable not set.")
    st.stop()


# -------------------------
# GLOBAL CSS
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Bebas+Neue&display=swap" rel="stylesheet">

<style>
.stApp, body, .block-container {
    background-color: #000000 !important;
}

.header-img {
    width: 100%;
    height: 380px;
    object-fit: cover;
}

.header-title {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Anton', sans-serif;
    font-size: 70px;
    color: white;
    text-shadow: 4px 4px 12px #000;
    letter-spacing: 4px;
}

.main-card {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

label {
    font-family: 'Anton', sans-serif !important;
    font-size: 22px !important;
    color: #F0B940 !important;
}

.sublabel {
    font-size: 14px;
    color: #CCCCCC;
    opacity: 0.75;
    margin-top: -6px;
    margin-bottom: 12px;
}

.stTextInput input, .stSelectbox div {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

div.stButton {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}

div.stButton > button {
    background-image: url('https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg');
    background-size: cover;
    width: 300px;
    height: 60px;
    border: 3px solid #C34023;
    border-radius: 10px;
    color: white;
    font-family: 'Anton', sans-serif;
    font-size: 26px;
    letter-spacing: 3px;
    text-shadow: 2px 2px 5px #000;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="position: relative; text-align: center;">
    <img class="header-img" src="https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg">
    <div class="header-title">PHOENIX SUNS</div>
</div>
""", unsafe_allow_html=True)


# -------------------------
# EXPLANATION FUNCTION
# -------------------------
def generate_explanation(features, prob):
    explanation = []
    explanation.append("The model predicts a WIN primarily because:" if prob >= 0.5
                       else "The model predicts a LOSS because:")

    if features["opp_streak"] >= 2:
        explanation.append("Opponent is on a winning streak.")
    if features["suns_streak"] <= -1:
        explanation.append("Suns enter on a losing streak.")
    if features["location"] == "Home":
        explanation.append("Home court advantage.")
    if features["suns_rest"] > features["opp_rest"]:
        explanation.append("Suns have more rest days.")

    if len(explanation) == 1:
        explanation.append("Multiple small factors influence the model’s prediction.")

    return explanation


# -------------------------
# INPUT FORM
# -------------------------
st.subheader("Game Inputs")

col1, col2 = st.columns(2)

with col1:
    location = st.selectbox("Location", ["Home", "Away"])
    suns_streak_raw = st.text_input("Suns' Streak", placeholder="-2 or 3")
    st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)
    suns_rest = st.number_input("Suns’ Rest Days", min_value=1, step=1, value=1)

with col2:
    opponent = st.selectbox("Opponent", [
        "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW",
        "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK",
        "OKC","ORL","PHI","POR","SAC","SAS","TOR","UTA","WAS"
    ])
    opp_streak_raw = st.text_input("Opponent Streak", placeholder="-1 or 4")
    st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)
    opp_rest = st.number_input("Opponent Rest Days", min_value=1, step=1, value=1)

predict_pressed = st.button("PREDICT")


# -------------------------
# HELPER
# -------------------------
def extract_prob(resp):
    for key in ["predictions", "outputs", "results", "data"]:
        if key in resp:
            val = resp[key]
            if isinstance(val, list):
                return float(val[0][0] if isinstance(val[0], list) else val[0])
    return None


# -------------------------
# PREDICTION
# -------------------------
if predict_pressed:
    try:
        suns_streak = int(suns_streak_raw)
        opp_streak = int(opp_streak_raw)
    except:
        st.error("Please enter valid streak numbers.")
        st.stop()

    payload = {
        "dataframe_records": [{
            "opponent": opponent,
            "location": location,
            "suns_streak": suns_streak,
            "opp_streak": opp_streak,
            "suns_rest": suns_rest,
            "opp_rest": opp_rest
        }]
    }

    with st.spinner("Contacting model…"):
        r = requests.post(
            ENDPOINT_URL,
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        try:
            r.raise_for_status()
            resp = r.json()
            prob = extract_prob(resp)
        except:
            st.error("Model response error.")
            st.json(resp)
            st.stop()

    result = "WIN" if prob >= 0.5 else "LOSS"
    color = "#f3d221" if result == "WIN" else "#e0357f"

    st.markdown(f"""
        <h2 style="color:{color}; font-family:Anton;">
            Suns {result}!
        </h2>
        <div style="color:white; font-size:24px;">
            Win Probability: {prob:.3f}
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Why This Prediction?")
    for line in generate_explanation(payload["dataframe_records"][0], prob):
        st.markdown(f"- {line}")


# -------------------------
# FOOTER
# -------------------------
st.markdown("""
<hr style="border:1px solid #333; margin-top:50px;">

<div style="
    text-align:center;
    color:#AAAAAA;
    font-family: Arial, sans-serif;
    font-size:14px;
    line-height:1.6;
">
    <strong style="font-size:16px; color:#F0B940;">Rana Baranski</strong><br>
    CIS 508 – Fall 2025<br><br>

    <em>
    This project is an academic demonstration created for educational purposes only.
    It is not affiliated with, endorsed by, or sponsored by the Phoenix Suns, the NBA,
    or any related organizations. Team names, logos, and images are used solely for
    illustrative purposes and are not intended to infringe upon any copyrighted material.
    </em>
</div>
""", unsafe_allow_html=True)
