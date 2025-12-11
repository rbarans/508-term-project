# -------------------------
# Your Streamlit App
# -------------------------

import streamlit as st
import requests
import os

ENDPOINT_URL = "https://dbc-b6951fe2-dfb1.cloud.databricks.com/serving-endpoints/tem-project_rana/invocations"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

st.set_page_config(page_title="Suns Predictor", layout="wide")

st.markdown(
    """
    <style>
        body { background-color: #000; color: white; }
        .title { font-family: 'Anton', sans-serif; letter-spacing: 3px;
                 font-size: 50px; text-align: center; color: #fff;
                 text-shadow: 3px 3px 10px black; }
        .header-image {
            width: 100%; height: 370px;
            background-image: url('https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg');
            background-size: cover;
            background-position: center 60%;
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="header-image"></div>', unsafe_allow_html=True)
st.markdown('<div class="title">PHOENIX SUNS</div>', unsafe_allow_html=True)

# Input form
st.subheader("Game Prediction Inputs")

col1, col2 = st.columns(2)

with col1:
    location = st.selectbox("Location", ["Home", "Away"])
    suns_streak = st.number_input("Suns' Streak", step=1, format="%d")
    suns_rest = st.number_input("Suns' Rest Days", step=1, min_value=1, format="%d")

with col2:
    opponent = st.selectbox("Opponent", [
        "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW","HOU","IND",
        "LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI","POR",
        "SAC","SAS","TOR","UTA","WAS"
    ])
    opp_streak = st.number_input("Opponent's Streak", step=1, format="%d")
    opp_rest = st.number_input("Opponent's Rest Days", step=1, min_value=1, format="%d")

if st.button("Predict", use_container_width=True):

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

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    with st.spinner("Contacting prediction server..."):
        r = requests.post(ENDPOINT_URL, headers=headers, json=payload)

    if r.status_code != 200:
        st.error(f"Databricks error: {r.text}")
        st.stop()

    db_response = r.json()
    prob = db_response["predictions"][0]


    # EXPLANATION GENERATOR (same as Flask)
    def generate_explanation(features, prob):
        opp = features["opponent"]
        loc = features["location"]
        ss = features["suns_streak"]
        os = features["opp_streak"]
        sr = features["suns_rest"]
        orr = features["opp_rest"]

        explanation = []

        if prob >= 0.5:
            explanation.append("The model predicts a WIN primarily because:")
        else:
            explanation.append("The model predicts a LOSS because:")

        if os >= 3:
            explanation.append(f"Opponent on strong +{os} streak.")
        elif os == 2:
            explanation.append("Opponent on a +2 streak.")
        elif os == 1:
            explanation.append("Opponent has mild momentum (+1).")
        elif os <= -2:
            explanation.append(f"Opponent struggling ({os}).")
        elif os == -1:
            explanation.append("Opponent slightly struggling.")

        if ss >= 2:
            explanation.append(f"Suns on a +{ss} streak.")
        elif ss == 1:
            explanation.append("Suns have mild momentum (+1).")
        elif ss <= -1:
            explanation.append(f"Suns losing streak ({ss}).")

        rest_diff = sr - orr

        if sr >= 3:
            explanation.append(f"Suns long rest ({sr} days).")
        elif rest_diff > 0:
            explanation.append(f"Suns rest advantage ({sr} vs {orr}).")
        elif rest_diff == 0:
            explanation.append("Equal rest for both teams.")
        else:
            explanation.append(f"Opponent rest advantage ({orr} vs {sr}).")

        if loc == "Home":
            explanation.append("Home court advantage.")
        else:
            explanation.append("Away game disadvantage.")

        return explanation


    features = payload["dataframe_records"][0]
    explanation = generate_explanation(features, prob)

    # Display result
    st.subheader("Prediction Result")

    if prob >= 0.5:
        st.success(f"WIN • Probability: {prob:.3f}")
    else:
        st.error(f"LOSS • Probability: {prob:.3f}")

    st.write("---")
    st.write("### Explanation")
    for line in explanation:
        st.write(f"- {line}")
