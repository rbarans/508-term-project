import streamlit as st
import requests
import os

ENDPOINT_URL = "https://dbc-b6951fe2-dfb1.cloud.databricks.com/serving-endpoints/tem-project_rana/invocations"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

st.set_page_config(page_title="Suns' Game Predictor", layout="centered")

# ---------------------------------------------------
# Custom styling (keeps aesthetic similarity)
# ---------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #000;
}
label {
    font-size: 22px !important;
    color: #F0B940 !important;
    font-family: 'Anton', sans-serif !important;
}
.small-label {
    font-size: 14px;
    color: #ccc;
    opacity: 0.75;
    margin-top: -10px;
    margin-bottom: 10px;
    font-family: Arial, sans-serif;
}
.big-title {
    font-size: 64px;
    font-family: 'Anton', sans-serif;
    color: white;
    text-align: center;
    text-shadow: 5px 5px 12px #000;
    letter-spacing: 4px;
}
.container {
    background-color: #0d0d0d;
    border: 4px solid #362B4D;
    box-shadow: 0 0 30px #5C2E52;
    padding: 25px;
}
</style>
""", unsafe_allow_html=True)

# Header Image + Title
st.image(
    "https://raw.githubusercontent.com/rbarans/508-term-project/refs/heads/main/valley.jpg",
    use_column_width=True
)
st.markdown("<div class='big-title'>PHOENIX SUNS</div>", unsafe_allow_html=True)
st.write("")

# ---------------------------------------------------
# Explanation Logic
# ---------------------------------------------------
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

    # Opponent streak
    if os_ >= 3:
        explanation.append(
            f"The opponent is on a strong positive streak (+{os_}), which the model heavily associates with Suns losses."
        )
    elif os_ == 2:
        explanation.append("The opponent has a +2 streak, which slightly reduces Suns win probability.")
    elif os_ == 1:
        explanation.append("The opponent has a mild winning streak (+1), giving them slight momentum.")
    elif os_ <= -2:
        explanation.append(f"The opponent has been struggling (streak {os_}), increasing Suns' chances.")
    elif os_ == -1:
        explanation.append("The opponent has a small losing streak, slightly benefiting the Suns.")

    # Suns streak
    if ss >= 2:
        explanation.append(f"The Suns are on a +{ss} winning streak, which contributes positively.")
    elif ss == 1:
        explanation.append("The Suns enter with mild positive momentum (+1).")
    elif ss <= -1:
        explanation.append(f"The Suns have a losing streak ({ss}), which pulls prediction downward.")

    # Rest advantage
    rest_diff = sr - orr

    if sr >= 3:
        explanation.append(
            f"The Suns have {sr} rest days. Historically, long rest (3+) unexpectedly correlates with lower win probability."
        )
    elif rest_diff > 0:
        explanation.append(f"The Suns have more rest ({sr} vs {orr}), modestly improving the prediction.")
    elif rest_diff == 0:
        explanation.append("Both teams have equal rest, giving no advantage.")
    else:
        explanation.append(f"The opponent has more rest ({orr} vs {sr}), reducing Suns' chances.")

    # Home/Away
    if loc == "Home":
        explanation.append("Playing at home provides a small benefit.")
    else:
        explanation.append("Playing away slightly lowers Suns win probability.")

    # Clean explanation for WIN
    if prob >= 0.5:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(word in line.lower() for word in [
                "loss", "losing", "reduces", "lower",
                "strong positive streak", "pulls", "heavily associates"
            ]):
                continue
            cleaned.append(line)

        if len(cleaned) == 1:
            cleaned.append("Several factors modestly support the Suns in this matchup.")

        explanation = cleaned

    # Clean explanation for LOSS
    else:
        cleaned = [explanation[0]]
        for line in explanation[1:]:
            if any(word in line.lower() for word in [
                "loss", "losing", "reduces", "lower", "strong positive streak"
            ]):
                cleaned.append(line)

        if len(cleaned) == 1:
            cleaned.append("Several model-learned factors tilt the prediction toward a loss.")

        explanation = cleaned

    return explanation

# ---------------------------------------------------
# UI Container
# ---------------------------------------------------
with st.container():
    st.markdown("<div class='container'>", unsafe_allow_html=True)

    st.subheader("Game Inputs")

    col1, col2 = st.columns(2)

    with col1:
        location = st.selectbox("Location", ["Home", "Away"])
        opponent = st.selectbox(
            "Opponent",
            ["ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW","HOU","IND",
             "LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI","POR",
             "SAC","SAS","TOR","UTA","WAS"]
        )
        st.markdown("<div class='small-label'>Losses represented with (-)</div>", unsafe_allow_html=True)
        suns_streak = st.number_input("Suns' Streak", step=1)

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='small-label'>Losses represented with (-)</div>", unsafe_allow_html=True)
        opp_streak = st.number_input("Opponent Streak", step=1)

        suns_rest = st.number_input("Suns' Rest Days", min_value=1, step=1)
        opp_rest = st.number_input("Opponent Rest Days", min_value=1, step=1)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# Predict Button
# ---------------------------------------------------
if st.button("PREDICT", use_container_width=True):
    with st.spinner("Contacting model..."):
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
            st.error(f"Databricks Error: {e}")
            st.stop()

    prediction = "WIN" if prob >= 0.5 else "LOSS"
    color = "#f3d221" if prediction == "WIN" else "#e0357f"

    st.markdown(f"""
    ### Prediction for: **Suns vs {opponent}**

    **<span style='color:{color}; font-size:28px;'>{prediction}</span>**  
    Win Probability: **{prob:.3f}**
    """, unsafe_allow_html=True)

    explanation = generate_explanation(payload["dataframe_records"][0], prob)

    st.write("---")
    st.subheader("Explanation")
    st.write(explanation[0])
    st.markdown("<ul>", unsafe_allow_html=True)
    for line in explanation[1:]:
        st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
