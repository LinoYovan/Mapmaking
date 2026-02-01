import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Create Maps",
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
    
    .main {
        background: transparent !important;
    }
    
    .stMainBlockContainer {
        background: transparent !important;
    }
    
    html, body {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 40px 20px;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
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

# Hide Streamlit UI
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Main content
st.markdown("""
<div class="main-container">
    <div class="header-section">
        <h1 class="main-title">🗺️ GeoSpatial Mapping Suite</h1>
        <p class="subtitle">Geospatial Visualization Tools</p>
    </div>
    
    <div class="cards-container">
        <div class="card">
            <span class="card-icon">🗺️</span>
            <h2 class="card-title">Single Map Generator</h2>
            <p class="card-description">Create a single high-quality map with interpolated sampling points.</p>
            <div class="card-features">
                <ul>
                    <li>RBF interpolation</li>
                    <li>Single snapshot mapping</li>
                    <li>Customizable labels</li>
                    <li>Multiple export formats</li>
                    <li>Publication-ready output</li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <span class="card-icon">📊</span>
            <h2 class="card-title">Multi-Map Grid</h2>
            <p class="card-description">Generate multiple maps in a grid layout for seasonal or time-series data.</p>
            <div class="card-features">
                <ul>
                    <li>Batch processing</li>
                    <li>Customizable grid layout</li>
                    <li>Consistent color scaling</li>
                    <li>Interactive controls</li>
                    <li>Professional styling</li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <span class="card-icon">✨</span>
            <h2 class="card-title">Interactive Animator</h2>
            <p class="card-description">Create animated GIFs showing time-series data with interactive controls.</p>
            <div class="card-features">
                <ul>
                    <li>Interactive month selection</li>
                    <li>Customizable interpolation</li>
                    <li>GIF animation generation</li>
                    <li>Real-time adjustment</li>
                    <li>PNG export option</li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="info-section">
        <div class="divider"></div>
        <p>📌 Use the sidebar or click a card above to select an application</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.header("🗺️ Navigation")
    
    selected = st.radio(
        "Choose a tool:",
        ["📌 Home", "🗺️ Single Map", "📊 Multi-Map Grid", "✨ Animator"],
        index=0
    )
    
    if selected == "🗺️ Single Map":
        st.switch_page("pages/1_single_map.py")
    elif selected == "📊 Multi-Map Grid":
        st.switch_page("pages/2_multi_map_grid.py")
    elif selected == "✨ Animator":
        st.switch_page("pages/3_animator.py")
