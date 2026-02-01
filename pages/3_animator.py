import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from scipy.interpolate import Rbf
import matplotlib.patches as mpatches
from datetime import datetime
import tempfile
import os
import zipfile
import imageio
from PIL import Image
import io

# Set page configuration
st.set_page_config(
    page_title="AQI Animator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #667eea;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #667eea;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #667eea;
        color: white;
    }
    .stButton>button:hover {
        background-color: #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# App title with back button
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("← Back to Menu"):
        st.switch_page("pages/menu.py")
with col2:
    st.markdown('<h1 class="main-header">✨ Interactive Animator</h1>', unsafe_allow_html=True)

# Initialize session state for storing data
if 'gdf_boundary' not in st.session_state:
    st.session_state.gdf_boundary = None
if 'gdf_points' not in st.session_state:
    st.session_state.gdf_points = None
if 'global_vmin' not in st.session_state:
    st.session_state.global_vmin = None
if 'global_vmax' not in st.session_state:
    st.session_state.global_vmax = None

# Sidebar for user inputs
with st.sidebar:
    st.header("📤 Upload Data")
    
    # File uploaders
    csv_file = st.file_uploader("Upload CSV File", type=['csv'])
    
    # Shapefile upload
    st.subheader("Shapefile Upload")
    shapefile_zip = st.file_uploader(
        "Upload Shapefile ZIP (containing .shp, .shx, .dbf, etc.)",
        type=['zip'],
        help="Upload a ZIP file containing all shapefile components"
    )
    
    st.header("⚙️ Visualization Settings")
    
    # Column names
    x_col = st.text_input("X Coordinate Column", "x")
    y_col = st.text_input("Y Coordinate Column", "y")
    data_col = st.text_input("Data Column", "AQI")
    date_col = st.text_input("Date Column", "Date")
    
    # Interpolation settings
    st.subheader("Interpolation Settings")
    interpolation_resolution = st.slider("Resolution", 100, 500, 300)
    rbf_function = st.selectbox(
        "RBF Function",
        ['multiquadric', 'inverse', 'gaussian', 'linear', 'cubic', 'quintic', 'thin_plate'],
        index=2
    )
    rbf_smooth = st.slider("Smoothing", 0.0, 1.0, 0.1)
    
    # Display options
    st.subheader("Display Options")
    show_points = st.checkbox("Show Sample Points", True)
    show_colorbar = st.checkbox("Show Colorbar", True)
    show_scalebar = st.checkbox("Show Scalebar", True)
    show_north_arrow = st.checkbox("Show North Arrow", True)
    show_labels = st.checkbox("Show Point Labels", False)
    
    # Color settings
    st.subheader("Color Settings")
    colormap = st.selectbox(
        "Colormap",
        plt.colormaps(),
        index=plt.colormaps().index('inferno') if 'inferno' in plt.colormaps() else 0
    )
    
    # GIF settings
    st.subheader("Animation Settings")
    frame_duration = st.slider("Frame Duration (seconds)", 0.1, 2.0, 0.5)
    output_folder = st.text_input("Output Folder for GIF", "output_animations")
    
    # Month selection
    st.subheader("Month Selection")
    months = st.multiselect(
        "Select months to display",
        list(range(1, 13)),
        default=list(range(1, 13)),
        format_func=lambda x: datetime(2023, x, 1).strftime('%B')
    )

# Helper functions
def create_interpolation_grid(gdf_boundary, resolution):
    bounds = gdf_boundary.total_bounds
    xi = np.linspace(bounds[0], bounds[2], resolution)
    yi = np.linspace(bounds[1], bounds[3], resolution)
    xi, yi = np.meshgrid(xi, yi)
    
    polygon = gdf_boundary.geometry.iloc[0]
    points = np.column_stack((xi.ravel(), yi.ravel()))
    inside_mask = np.array([polygon.contains(Point(x, y)) for x, y in points]).reshape(xi.shape)
    
    return xi, yi, inside_mask

def perform_interpolation(points_df, xi, yi, inside_mask, data_column, rbf_function, rbf_smooth):
    xi_inside = xi[inside_mask]
    yi_inside = yi[inside_mask]
    
    rbf = Rbf(points_df[x_col], points_df[y_col], points_df[data_column], 
              function=rbf_function, smooth=rbf_smooth)
    zi_rbf = rbf(xi_inside, yi_inside)
    
    zi_full = np.full_like(xi, np.nan)
    zi_full[inside_mask] = zi_rbf
    
    return np.ma.masked_where(~inside_mask, zi_full)

def create_plot(gdf_boundary, gdf_points, xi, yi, zi_masked, title_text, vmin, vmax):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    gdf_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
    
    if colormap not in plt.colormaps():
        cmap = 'viridis'
    else:
        cmap = colormap
    
    levels = np.linspace(vmin, vmax, 20)
    c = ax.contourf(xi, yi, zi_masked, levels=levels, cmap=cmap, alpha=0.75, vmin=vmin, vmax=vmax)
    
    if show_points:
        gdf_points.plot(ax=ax, color='blue', markersize=50, marker='o', edgecolor='black', linewidth=1)
    
    if show_labels and show_points:
        for idx, row in gdf_points.iterrows():
            ax.text(row.geometry.x, row.geometry.y + 200, f"{row[data_col]:.0f}", 
                   color='white', fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='blue', alpha=0.7))
    
    if show_scalebar:
        bounds = gdf_boundary.total_bounds
        x0 = bounds[0] + (bounds[2] - bounds[0]) * 0.05
        y0 = bounds[1] + (bounds[3] - bounds[1]) * 0.05
        scalebar_length = 5000
        
        ax.plot([x0, x0 + scalebar_length], [y0, y0], color='black', lw=4)
        ax.text(x0 + scalebar_length / 2, y0 - (bounds[3] - bounds[1]) * 0.02, 
                f'{scalebar_length/1000:.0f} km', ha='center', va='top', fontsize=12)
    
    if show_north_arrow:
        bounds = gdf_boundary.total_bounds
        arrow_x = bounds[0] + (bounds[2] - bounds[0]) * 0.95
        arrow_y = bounds[1] + (bounds[3] - bounds[1]) * 0.95
        
        ax.annotate('N', xy=(arrow_x, arrow_y), xytext=(0, -20), 
                   textcoords='offset points', ha='center', va='top', 
                   fontsize=14, fontweight='bold', color='black',
                   arrowprops=dict(arrowstyle='-|>', linewidth=2, color='black'))
    
    ax.set_title(title_text, fontsize=16, pad=20)
    
    if show_colorbar:
        cbar = plt.colorbar(c, ax=ax, orientation='vertical', location='right', shrink=0.6, pad=0.15)
        cbar.set_label(data_col, fontsize=14, fontweight='bold')
        cbar.ax.tick_params(labelsize=12, width=2, length=6)
        
        tick_values = np.linspace(vmin, vmax, 6)
        cbar.set_ticks(tick_values)
        cbar.set_ticklabels([f'{val:.0f}' for val in tick_values])
        cbar.outline.set_linewidth(2)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    plt.tight_layout()
    return fig

def extract_and_load_shapefile(zip_file):
    if not zip_file:
        return None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_file.getbuffer())
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        
        shp_file_path = None
        for file in os.listdir(tmpdir):
            if file.endswith('.shp'):
                shp_file_path = os.path.join(tmpdir, file)
                break
        
        if shp_file_path:
            try:
                gdf = gpd.read_file(shp_file_path)
                st.success(f"✓ Shapefile loaded: {os.path.basename(shp_file_path)}")
                return gdf
            except Exception as e:
                st.error(f"Error reading shapefile: {e}")
                st.info(f"Files in ZIP: {', '.join(os.listdir(tmpdir))}")
                return None
        else:
            st.error("No .shp file found in the uploaded ZIP archive")
            st.info(f"Files in ZIP: {', '.join(os.listdir(tmpdir))}")
            return None

def save_plot_to_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return buf

def create_gif_animation(frame_paths, output_path, frame_duration):
    images = []
    for frame_path in frame_paths:
        images.append(imageio.imread(frame_path))
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    duration_ms = int(frame_duration * 1000)
    
    with imageio.get_writer(output_path, mode='I', duration=duration_ms, loop=0) as writer:
        for image in images:
            writer.append_data(image)
    
    return output_path

# Process uploaded files
shapefile_loaded = False

if csv_file and shapefile_zip:
    df = pd.read_csv(csv_file)
    
    df[date_col] = pd.to_datetime(df[date_col])
    df['month'] = df[date_col].dt.month
    df['year'] = df[date_col].dt.year
    
    df["geometry"] = df.apply(lambda row: Point(row[x_col], row[y_col]), axis=1)
    gdf_points = gpd.GeoDataFrame(df, geometry="geometry")
    
    gdf_boundary = extract_and_load_shapefile(shapefile_zip)
    
    if gdf_boundary is not None:
        st.session_state.gdf_boundary = gdf_boundary
        st.session_state.gdf_points = gdf_points
        st.session_state.global_vmin = df[data_col].min()
        st.session_state.global_vmax = df[data_col].max()
        shapefile_loaded = True

# Display visualization if data is loaded
if shapefile_loaded and st.session_state.gdf_boundary is not None and st.session_state.gdf_points is not None:
    st.markdown('<h2 class="section-header">📊 Visualization</h2>', unsafe_allow_html=True)
    
    xi, yi, inside_mask = create_interpolation_grid(
        st.session_state.gdf_boundary, 
        interpolation_resolution
    )
    
    selected_month = st.selectbox(
        "Select a month to visualize",
        options=months,
        format_func=lambda x: datetime(2023, x, 1).strftime('%B')
    )
    
    month_data = st.session_state.gdf_points[st.session_state.gdf_points['month'] == selected_month]
    
    if not month_data.empty:
        zi_masked = perform_interpolation(
            month_data, xi, yi, inside_mask, data_col, 
            rbf_function, rbf_smooth
        )
        
        month_name = datetime(2023, selected_month, 1).strftime('%B %Y')
        title_text = f"{month_name}\n{data_col} Distribution"
        
        fig = create_plot(
            st.session_state.gdf_boundary, month_data, xi, yi, zi_masked, 
            title_text, st.session_state.global_vmin, st.session_state.global_vmax
        )
        
        st.pyplot(fig)
        
        col1, col2 = st.columns(2)
        
        with col1:
            buf = save_plot_to_buffer(fig)
            st.download_button(
                label="📥 Download as PNG",
                data=buf,
                file_name=f"aqi_visualization_{selected_month}.png",
                mime="image/png"
            )
        
        with col2:
            if st.button("🎬 Create GIF Animation for All Months"):
                with st.spinner("Creating animation... This may take a while."):
                    temp_dir = tempfile.mkdtemp()
                    frame_paths = []
                    
                    progress_bar = st.progress(0)
                    
                    for idx, month in enumerate(months):
                        month_data = st.session_state.gdf_points[st.session_state.gdf_points['month'] == month]
                        if not month_data.empty:
                            zi_masked = perform_interpolation(
                                month_data, xi, yi, inside_mask, data_col, 
                                rbf_function, rbf_smooth
                            )
                            
                            month_name = datetime(2023, month, 1).strftime('%B %Y')
                            title_text = f"{month_name}\n{data_col} Distribution"
                            
                            frame_fig = create_plot(
                                st.session_state.gdf_boundary, month_data, xi, yi, zi_masked, 
                                title_text, st.session_state.global_vmin, st.session_state.global_vmax
                            )
                            
                            frame_path = os.path.join(temp_dir, f"frame_{month:02d}.png")
                            frame_fig.savefig(frame_path, dpi=100, bbox_inches='tight')
                            plt.close(frame_fig)
                            frame_paths.append(frame_path)
                        
                        progress_bar.progress((idx + 1) / len(months))
                    
                    os.makedirs(output_folder, exist_ok=True)
                    gif_path = os.path.join(output_folder, "aqi_animation.gif")
                    
                    total_duration = len(frame_paths) * frame_duration
                    st.info(f"🎞️ Creating GIF: {len(frame_paths)} frames @ {frame_duration}s/frame = {total_duration:.1f}s total")
                    
                    create_gif_animation(frame_paths, gif_path, frame_duration)
                    
                    for frame_path in frame_paths:
                        os.remove(frame_path)
                    os.rmdir(temp_dir)
                    
                    st.success(f"✓ GIF saved to: {gif_path}")
                    st.image(gif_path, caption="Generated GIF Animation", use_column_width=True)
                    
                    with open(gif_path, "rb") as gif_file:
                        st.download_button(
                            label="📥 Download GIF Animation",
                            data=gif_file,
                            file_name="aqi_animation.gif",
                            mime="image/gif"
                        )
    else:
        st.warning(f"⚠️ No data available for the selected month: {selected_month}")
else:
    st.info("📌 Please upload CSV file and Shapefile ZIP to begin visualization")

# Information section
with st.expander("ℹ️ How to Use", expanded=False):
    st.markdown("""
    **Quick Start:**
    1. Upload your CSV file with AQI data
    2. Upload a ZIP file containing shapefile components
    3. Select visualization options
    4. Choose a month to view
    5. Download PNG or create GIF animations
    
    **Tips:**
    - Adjust smoothing for more/less detail
    - Change RBF function for different interpolation styles
    - Higher resolution = smoother but slower
    """)
