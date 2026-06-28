import streamlit as st
from app.components.hero_3d import render_hero_3d
st.markdown(render_hero_3d(80, 10, '2026-06-28'), unsafe_allow_html=True)
