import streamlit as st

st.set_page_config(
    page_title="Weather Advisor",
    page_icon="⛈",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("forecast.py", title="Weather Forecast", icon="🌍"),
    st.Page("historical.py", title="Historical Rain Report", icon="🌧")
])

pg.run()
