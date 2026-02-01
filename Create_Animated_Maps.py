import streamlit as st
from streamlit_option_menu import option_menu
import os

# Set page configuration
st.set_page_config(
    page_title="GeoSpatial Mapping Suite",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for polished design
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: transparent !important;
    }
    
    .stMainBlockContainer {
        background: transparent !important;
    }
    
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 40px 20px;
    }
    
    .header-section {
        text-align: center;
        margin-bottom: 60px;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 15px;
        letter-spacing: -1px;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #b0bec5;
        margin-bottom: 40px;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    .cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 40px;
        max-width: 900px;
        width: 100%;
    }
    
    .card {
        position: relative;
        padding: 40px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.23, 1, 0.320, 1);
        overflow: hidden;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }
    
    .card:hover::before {
        left: 100%;
    }
    
    .card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }
    
    .card-icon {
        font-size: 3rem;
        margin-bottom: 20px;
        display: block;
    }
    
    .card-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 15px;
    }
    
    .card-description {
        font-size: 1rem;
        color: #b0bec5;
        line-height: 1.6;
        margin-bottom: 25px;
    }
    
    .card-features {
        font-size: 0.85rem;
        color: #90a4ae;
        margin-bottom: 25px;
        padding: 15px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        border-left: 3px solid rgba(255, 255, 255, 0.2);
    }
    
    .card-features li {
        margin-bottom: 8px;
        margin-left: 20px;
    }
    
    .card-button {
        width: 100%;
        padding: 14px 28px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    
    .card:nth-child(2) .card-button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .card-button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    .card:nth-child(2) .card-button:hover {
        box-shadow: 0 10px 20px rgba(245, 87, 108, 0.4);
    }
    
    .info-section {
        margin-top: 80px;
        text-align: center;
        color: #b0bec5;
        font-size: 0.95rem;
    }
    
    .divider {
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
        margin: 40px 0;
        max-width: 200px;
        margin-left: auto;
        margin-right: auto;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
        }
        
        .cards-container {
            gap: 25px;
        }
        
        .card {
            padding: 30px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Hide default Streamlit UI elements
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Main content
st.markdown("""
<div style="text-align: center; margin-bottom: 40px;">
    <h1 style="font-size: 3rem; color: #ffffff; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);">🗺️ GeoSpatial Mapping Suite</h1>
    <p style="font-size: 1.2rem; color: #b0bec5;">Advanced Air Quality Visualization Tools</p>
</div>
""", unsafe_allow_html=True)

# Create three columns for the tools
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: rgba(31, 119, 180, 0.1); border-radius: 10px;">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">🗺️</div>
        <h3 style="color: #1f77b4; margin: 10px 0;">Single Map Generator</h3>
        <p style="font-size: 0.85rem; color: #666; margin: 5px 0;">Create a single high-quality map</p>
        <ul style="text-align: left; font-size: 0.8rem; color: #666; margin: 10px 0; padding-left: 15px;">
            <li>RBF interpolation</li>
            <li>Customizable labels</li>
            <li>Multiple formats</li>
            <li>Publication-ready</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch", key="btn_single", use_container_width=True):
        st.switch_page("pages/1_single_map.py")

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: rgba(102, 126, 234, 0.1); border-radius: 10px;">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">📊</div>
        <h3 style="color: #667eea; margin: 10px 0;">Multi-Map Grid</h3>
        <p style="font-size: 0.85rem; color: #666; margin: 5px 0;">Multiple maps in grid layout</p>
        <ul style="text-align: left; font-size: 0.8rem; color: #666; margin: 10px 0; padding-left: 15px;">
            <li>Batch processing</li>
            <li>Grid customization</li>
            <li>Consistent scaling</li>
            <li>Professional styling</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch", key="btn_multi", use_container_width=True):
        st.switch_page("pages/2_multi_map_grid.py")

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: rgba(245, 87, 108, 0.1); border-radius: 10px;">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">✨</div>
        <h3 style="color: #f5576c; margin: 10px 0;">Interactive Animator</h3>
        <p style="font-size: 0.85rem; color: #666; margin: 5px 0;">Animated GIFs from time-series</p>
        <ul style="text-align: left; font-size: 0.8rem; color: #666; margin: 10px 0; padding-left: 15px;">
            <li>Month selection</li>
            <li>Custom interpolation</li>
            <li>GIF generation</li>
            <li>PNG export</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch", key="btn_animator", use_container_width=True):
        st.switch_page("pages/3_animator.py")

st.markdown("""
<div style="text-align: center; margin-top: 40px; color: #888; font-size: 0.9rem;">
    <p>📌 Click a button above or use the sidebar menu to get started</p>
</div>
""", unsafe_allow_html=True)
