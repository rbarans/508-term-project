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
# GLOBAL CSS (Background, Fonts, Inputs, Button Fixes)
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Bebas+Neue&display=swap" rel="stylesheet">

<style>

/* True black background everywhere */
.stApp, body, .block-container {
    background-color: #000000 !important;
}

/* HEADER IMAGE */
.header-img {
    width: 100%;
    height: 380px;
    object-fit: cover;
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
    text-shadow: 4px 4px 12px #000;
    letter-spacing: 4px;
}

/* REMOVE PURPLE BOX AROUND INPUTS */
.main-card {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 10px 0;
}

/* LABEL STYLE */
label, .stSelectbox label, .stTextInput label {
    font-family: 'Anton', sans-serif !important;
    font-size: 22px !important;
    color: #F0B940 !important;
}

/* SUBLABEL STYLE */
.sublabel {
    font-size: 14px;
    font-family: Arial, sans-serif;
    color: #CCCCCC;
    opacity: 0.75;
    margin-top: -6px;
    margin-bottom: 12px;
}

/* FIX COLUMN WIDTHS */
div[data-testid="column"] > div {
    width: 100% !important;
}

/* TEXT INPUT BORDER */
.stTextInput > div > input {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

/* SELECT BORDER */
.stSelectbox > div > div {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
}

/* NUMBER INPUT BORDER (rest days only) */
.stNumberInput > div:first-child {
    border: 3px solid #7D344F !important;
    border-radius: 8px !important;
    background-color: #000 !important;
}

/* BUTTON CONTAINER FIX */
div.stButton {
    display: flex;
    justify-content: center;
    width: 100% !important;
    margin-top: 20px;
}

/* VALLEY THEMED BUTTON — NOW SCALES CORRECTLY */
div.stButton > button {
    background-image: url('https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg');
    background-size: cover;
    background-position: center 38%;
    background-repeat: no-repeat;

    width: 300px !important;
    height: 60px !important;

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
    transition: 0.15s ease-in-out;
}

</style>
""", unsafe_allow_html=True)


# -------------------------
# HEADER SECTION
# -------------------------
st.markdown("""
<div style="position: relative; text-align: center;">
    <img class="header-img" src="https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg">
    <div class="header-title">PHOENIX SUNS</div>
</div>
""", unsafe_allow_html=True)


# -------------------------
# EXPLANATION LOGIC (same as Flask version)
# -------------------------
def generate_explanation(features, prob):
    opp = features["opponent"]
    loc = features["location"]
    ss = features["suns_streak"]
    os_ = features["opp_streak"]
    sr = features["suns_rest"]
    orr = features["opp_rest"]

    explanation = []
    explanation.append("The model predicts a WIN primarily because:" if prob >= 0.5
                       else "The model predicts a LOSS because:")

    if os_ >= 3:
        explanation.append(f"Opponent on a strong winning streak (+{os_}), historically lowering Suns chances.")
    elif os_ == 2:
        explanation.append("Opponent has a +2 streak, slightly reducing Suns probability.")
    elif os_ == 1:
        explanation.append("Opponent holds mild momentum (+1).")
    elif os_ <= -2:
        explanation.append(f"Opponent is struggling (streak {os_}), increasing Suns probability.")
    elif os_ == -1:
        explanation.append("Opponent has a small losing streak.")

    if ss >= 2:
        explanation.append(f"Suns on a +{ss} streak, boosting the prediction.")
    elif ss == 1:
        explanation.append("Suns enter with mild momentum (+1).")
    elif ss <= -1:
        explanation.append(f"Suns losing streak ({ss}) lowers probability.")

    rest_diff = sr - orr
    if sr >= 3:
        explanation.append(f"{sr} rest days — long rest historically correlates with lower win probability.")
    elif rest_diff > 0:
        explanation.append(f"Suns have more rest ({sr} vs {orr}).")
    elif rest_diff == 0:
        explanation.append("Both teams have equal rest.")
    else:
        explanation.append(f"Opponent has more rest ({orr} vs {sr}).")

    if loc == "Home":
        explanation.append("Home court provides a small advantage.")
    else:
        explanation.append("Away games slightly reduce probability.")

    # WIN filter
    if prob >= 0.5:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if not any(w in line.lower() for w in ["loss", "lower", "reduces"]):
                cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors modestly support a Suns win.")
        return cleaned

    # LOSS filter
    else:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(w in line.lower() for w in ["loss", "lower", "reduces"]):
                cleaned.append(line)
        if len(cleaned) == 1:
            cleaned.append("Several factors tilt the model toward a loss.")
        return cleaned


# -------------------------
# INPUT FORM
# -------------------------
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.subheader("Game Inputs")

col1, col2 = st.columns(2)

# LEFT COLUMN
with col1:
    location = st.selectbox("Location", ["Home", "Away"])

    suns_streak_raw = st.text_input("Suns' Streak", value="", placeholder="e.g., -2 or 3")
    st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)

    suns_rest = st.number_input("Suns’ Rest Days", min_value=1, step=1)

# RIGHT COLUMN
with col2:
    opponent = st.selectbox("Opponent", [
        "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW",
        "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK",
        "OKC","ORL","PHI","POR","SAC","SAS","TOR","UTA","WAS"
    ])

    opp_streak_raw = st.text_input("Opponent Streak", value="", placeholder="e.g., -1 or 4")
    st.markdown('<div class="sublabel">Losses represented with (-)</div>', unsafe_allow_html=True)

    opp_rest = st.number_input("Opponent Rest Days", min_value=1, step=1)

predict_pressed = st.button("PREDICT")
st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# ON PREDICT CLICK
# -------------------------
if predict_pressed:

    # Convert streak strings → integers
    try:
        suns_streak = int(suns_streak_raw)
        opp_streak = int(opp_streak_raw)
    except:
        st.error("Please enter valid streak values (e.g., -2, 0, 3).")
        st.stop()

    payload = {
        "dataframe_records": [{
            "opponent": opponent,
            "location": location,
            "suns_streak": suns_streak,
            "opp_streak": opp_streak,
            "suns_rest": int(suns_rest),
            "opp_rest": int(opp_rest),
        }]
    }

    with st.spinner("Contacting model…"):
        r = requests.post(
            ENDPOINT_URL,
            headers={
                "Authorization": f"Bearer " + DATABRICKS_TOKEN,
                "Content-Type": "application/json",
            },
            json=payload
        )
        prob = r.json()["predictions"][0]

    result = "WIN" if prob >= 0.5 else "LOSS"
    color = "#f3d221" if result == "WIN" else "#e0357f"

    st.markdown(f"""
        <h2 style='color:{color}; font-family:Anton; text-shadow:2px 2px 5px #000;'>
            Suns {result}!
        </h2>
        <div style='color:white; font-family:Bebas Neue; font-size:24px;'>
            Win Probability: {prob:.3f}
        </div>
    """, unsafe_allow_html=True)

    explanation = generate_explanation(payload["dataframe_records"][0], prob)

    st.subheader("Why This Prediction?")
    for line in explanation:
        st.markdown(f"- {line}")