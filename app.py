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

/* HEADER IMAGE */
.header-img {
    width: 100%;
    height: 380px;
    object-fit: cover;
    border-bottom: 3px solid #362B4D;
}

/* TITLE OVERLAY */
.header-title {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Anton', sans-serif;
    font-size: 70px;
    color: white;
    text-shadow: 4px 4px 10px #000;
    letter-spacing: 4px;
}

/* Main card container */
.main-card {
    background-color: #0d0d0d;
    border: 4px solid #362B4D !important;
    box-shadow: 0 0 25px #5C2E52;
    padding: 25px 30px;
    border-radius: 12px;
    margin-top: 25px;
}

/* Labels */
label, .stSelectbox label, .stNumberInput label {
    font-family: 'Anton', sans-serif !important;
    font-size: 22px !important;
    color: #F0B940 !important;
}

/* Sublabels */
.sublabel {
    font-size: 14px;
    font-family: Arial, sans-serif;
    color: #CCCCCC;
    opacity: 0.75;
    margin-top: -8px;
    margin-bottom: 12px;
}

/* CLEAN INPUT BORDER */
.stNumberInput > div:first-child {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
}
.stNumberInput input {
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

.stSelectbox > div > div {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

/* FORCE STREAMLIT BUTTON CONTAINER TO BE WIDE */
div.stButton {
    display: flex;
    justify-content: center;   /* center horizontally */
    width: 100% !important;
    margin-top: 20px;
}

/* THEMED VALLEY BUTTON - NOW WORKS HORIZONTALLY */
div.stButton > button {
    background-image: url('https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg');
    background-size: cover;
    background-position: center 38%;
    background-repeat: no-repeat;

    width: 300px !important;       /* fixed horizontal size */
    height: 60px !important;       /* prevents vertical stacking */
    border: 3px solid #C34023 !important;
    border-radius: 10px;

    color: white !important;
    font-family: 'Anton', sans-serif !important;
    font-size: 26px !important;
    letter-spacing: 3px;

    display: flex;
    justify-content: center;
    align-items: center;

    text-shadow: 2px 2px 5px #000;
}

div.stButton > button:hover {
    transform: scale(1.05);
    transition: 0.15s ease;
}

/* FIX INPUT WIDTHS INSIDE COLUMNS */
div[data-testid="column"] > div {
    width: 100% !important;    /* force column to control width */
}

/* FIX NUMBER INPUT BORDERS WITHOUT BLEEDING */
.stNumberInput > div:first-child {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
}

.stNumberInput input {
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

/* FIX SELECT BOX WIDTH */
.stSelectbox > div > div {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}


</style>
""", unsafe_allow_html=True)



# -------------------------
# HEADER IMAGE + TITLE
# -------------------------
st.markdown("""
<div style="position: relative; text-align: center;">
    <img class="header-img" src="https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg">
    <div class="header-title">PHOENIX SUNS</div>
</div>
""", unsafe_allow_html=True)



# -------------------------
# EXPLANATION LOGIC
# (Identical behavior to your Flask version)
# -------------------------
def generate_explanation(features, prob):
    opp = features["opponent"]
    loc = features["location"]
    ss = features["suns_streak"]
    os_ = features["opp_streak"]
    sr = features["suns_rest"]
    orr = features["opp_rest"]

    explanation = []

    # WIN/LOSS intro
    explanation.append(
        "The model predicts a WIN primarily because:" if prob >= 0.5
        else "The model predicts a LOSS because:"
    )

    # Opponent streak
    if os_ >= 3:
        explanation.append(f"The opponent is on a strong positive streak (+{os_}), heavily reducing Suns chances.")
    elif os_ == 2:
        explanation.append("The opponent has a +2 streak, which slightly reduces Suns win probability.")
    elif os_ == 1:
        explanation.append("The opponent has a mild +1 winning streak.")
    elif os_ <= -2:
        explanation.append(f"The opponent is struggling (streak {os_}), increasing Suns chances.")
    elif os_ == -1:
        explanation.append("The opponent has a small losing streak, slightly benefiting the Suns.")

    # Suns streak
    if ss >= 2:
        explanation.append(f"The Suns are on a +{ss} streak, helping the prediction.")
    elif ss == 1:
        explanation.append("The Suns enter with +1 momentum.")
    elif ss <= -1:
        explanation.append(f"The Suns have a losing streak ({ss}), pulling the prediction toward a loss.")

    # Rest days
    rest_diff = sr - orr
    if sr >= 3:
        explanation.append(
            f"The Suns have {sr} rest days — historically long rest (3+) correlates with lower win probability."
        )
    elif rest_diff > 0:
        explanation.append(f"The Suns have a slight rest advantage ({sr} vs {orr}).")
    elif rest_diff == 0:
        explanation.append("Both teams have equal rest.")
    else:
        explanation.append(f"The opponent has more rest ({orr} vs {sr}), slightly reducing Suns chances.")

    # Location
    if loc == "Home":
        explanation.append("Home-court provides a small benefit.")
    else:
        explanation.append("Playing away slightly lowers Suns win probability.")

    # Filter explanation depending on WIN vs LOSS
    if prob >= 0.5:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(w in line.lower() for w in ["loss", "losing", "reduces", "lower"]):
                continue
            cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors modestly support the Suns in this matchup.")
        explanation = cleaned

    else:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(w in line.lower() for w in ["loss", "losing", "reduces", "lower"]):
                cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors tilt the model toward a loss.")
        explanation = cleaned

    return explanation



# -------------------------
# MAIN CARD CONTENT
# -------------------------
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

predict_button = st.button("PREDICT")
st.markdown("</div>", unsafe_allow_html=True)



# -------------------------
# MODEL CALL + RESULTS
# -------------------------
if predict_button:

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
        db_output = r.json()
        prob = db_output["predictions"][0]

    prediction = "WIN" if prob >= 0.5 else "LOSS"
    color = "#f3d221" if prediction == "WIN" else "#e0357f"

    st.markdown(f"""
        <h2 style='color:{color}; font-family:Anton; text-shadow:2px 2px 5px #000;'>
            Suns {prediction}!
        </h2>
        <div style='color:white; font-family:Bebas Neue; font-size:24px;'>
            Win Probability: {prob:.3f}
        </div>
    """, unsafe_allow_html=True)

    explanation = generate_explanation(payload["dataframe_records"][0], prob)

    st.subheader("Why This Prediction?")
    for line in explanation:
        st.markdown(f"- {line}")
