import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from scipy.interpolate import Rbf
from matplotlib import ticker
import matplotlib.patches as mpatches
import tempfile
import zipfile
import os
import io

st.set_page_config(
    page_title="Single Map Generator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #1f77b4;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    .stButton>button:hover {
        background-color: #0d47a1;
    }
</style>
""", unsafe_allow_html=True)

# Back button
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("← Back to Menu"):
        st.switch_page("pages/menu.py")
with col2:
    st.markdown('<h1 class="main-header">🗺️ Single Map Generator</h1>', unsafe_allow_html=True)

if 'gdf_boundary' not in st.session_state:
    st.session_state.gdf_boundary = None
if 'gdf_data' not in st.session_state:
    st.session_state.gdf_data = None
if 'df' not in st.session_state:
    st.session_state.df = None

def extract_shapefile(zip_file):
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
                return None
        else:
            st.error("No .shp file found in ZIP")
            return None

# Sidebar
with st.sidebar:
    st.header("📤 Upload Data")
    csv_file = st.file_uploader("Upload CSV File", type=['csv'])
    shapefile_zip = st.file_uploader("Upload Shapefile ZIP", type=['zip'])
    
    st.header("⚙️ Column Settings")
    x_col = st.text_input("X Coordinate Column", "x")
    y_col = st.text_input("Y Coordinate Column", "y")
    data_col = st.text_input("Data Column", "AQI")
    sample_name_col = st.text_input("Sample Name Column (optional)", "SampleName")
    
    st.header("🎨 Interpolation")
    resolution = st.slider("Resolution", 100, 500, 300)
    rbf_func = st.selectbox("RBF Function", 
        ['multiquadric', 'inverse', 'gaussian', 'linear', 'cubic', 'quintic', 'thin_plate'],
        index=2)
    rbf_smooth = st.slider("Smoothing", 0.0, 1.0, 0.1)
    contour_levels = st.slider("Contour Levels", 5, 50, 10)
    
    st.header("🖼️ Visualization")
    show_points = st.checkbox("Show Sample Points", True)
    show_labels = st.checkbox("Show Data Labels", True)
    show_sample_names = st.checkbox("Show Sample Names", False)
    show_scalebar = st.checkbox("Show Scalebar", True)
    show_north_arrow = st.checkbox("Show North Arrow", True)
    show_colorbar = st.checkbox("Show Colorbar", True)
    show_legend = st.checkbox("Show Legend", True)
    
    st.header("🎨 Colors & Style")
    colormap = st.selectbox("Colormap",
        plt.colormaps(),
        index=plt.colormaps().index('inferno') if 'inferno' in plt.colormaps() else 0)
    
    point_color = st.color_picker("Point Color", "#0000FF")
    label_color = st.color_picker("Label Color", "#FFFFFF")
    
    st.header("📏 Label Positions")
    label_offset_x = st.number_input("Label Offset X", -500, 500, 0)
    label_offset_y = st.number_input("Label Offset Y", -500, 500, 200)
    sample_name_offset_y = st.number_input("Sample Name Offset Y", -500, 500, -200)
    
    st.header("💾 Export")
    export_format = st.selectbox("Format", ['png', 'pdf', 'svg', 'jpg', 'tiff'])
    export_dpi = st.slider("DPI", 100, 300, 300)
    fig_width = st.slider("Figure Width (inches)", 4, 16, 8)
    fig_height = st.slider("Figure Height (inches)", 4, 12, 6)

# Process files
data_loaded = False
if csv_file and shapefile_zip:
    df = pd.read_csv(csv_file)
    gdf_boundary = extract_shapefile(shapefile_zip)
    
    if gdf_boundary is not None:
        df.dropna(subset=[x_col, y_col, data_col], inplace=True)
        df["geometry"] = df.apply(lambda row: Point(row[x_col], row[y_col]), axis=1)
        gdf_data = gpd.GeoDataFrame(df, geometry="geometry", crs=gdf_boundary.crs)
        
        st.session_state.gdf_boundary = gdf_boundary
        st.session_state.gdf_data = gdf_data
        st.session_state.df = df
        data_loaded = True

# Main visualization
if data_loaded and st.session_state.gdf_boundary is not None:
    st.markdown('<h2 class="section-header">📊 Generate Map</h2>', unsafe_allow_html=True)
    
    if st.button("🎨 Generate Map"):
        with st.spinner("Generating map..."):
            # Create grid
            bounds = st.session_state.gdf_boundary.total_bounds
            xi = np.linspace(bounds[0], bounds[2], resolution)
            yi = np.linspace(bounds[1], bounds[3], resolution)
            xi, yi = np.meshgrid(xi, yi)
            
            polygon = st.session_state.gdf_boundary.geometry.union_all()
            points = np.column_stack((xi.ravel(), yi.ravel()))
            inside_mask = np.array([polygon.contains(Point(x, y)) for x, y in points]).reshape(xi.shape)
            
            xi_inside = xi[inside_mask]
            yi_inside = yi[inside_mask]
            
            # RBF interpolation
            rbf = Rbf(st.session_state.df[x_col], st.session_state.df[y_col], 
                     st.session_state.df[data_col], function=rbf_func, smooth=rbf_smooth)
            zi_rbf = rbf(xi_inside, yi_inside)
            
            data_min = st.session_state.df[data_col].min()
            data_max = st.session_state.df[data_col].max()
            zi_rbf = np.clip(zi_rbf, data_min, data_max)
            
            zi_full = np.full_like(xi, np.nan)
            zi_full[inside_mask] = zi_rbf
            zi_masked = np.ma.masked_where(~inside_mask, zi_full)
            
            # Plot
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)
            st.session_state.gdf_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
            
            c = ax.contourf(xi, yi, zi_masked, levels=contour_levels, cmap=colormap, 
                           alpha=0.75, vmin=data_min, vmax=data_max)
            
            if show_points:
                ax.scatter(st.session_state.gdf_data.geometry.x, st.session_state.gdf_data.geometry.y,
                          c=point_color, s=50, marker='o', edgecolor='black', linewidth=1)
            
            if show_labels:
                for _, row in st.session_state.df.iterrows():
                    ax.text(row[x_col] + label_offset_x, row[y_col] + label_offset_y,
                           f"{row[data_col]:.0f}", color=label_color, fontsize=8,
                           ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=point_color, alpha=0.7))
            
            if show_sample_names and sample_name_col in st.session_state.df.columns:
                for _, row in st.session_state.df.iterrows():
                    ax.text(row[x_col], row[y_col] + sample_name_offset_y,
                           str(row[sample_name_col]), color='red', fontsize=8,
                           ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7))
            
            if show_scalebar:
                x0 = bounds[0] + (bounds[2] - bounds[0]) * 0.05
                y0 = bounds[1] + (bounds[3] - bounds[1]) * 0.05
                scalebar_length = 5000
                ax.plot([x0, x0 + scalebar_length], [y0, y0], color='black', lw=4)
                ax.text(x0 + scalebar_length / 2, y0 - (bounds[3] - bounds[1]) * 0.02,
                       f'{scalebar_length/1000:.0f} km', ha='center', va='top', fontsize=10)
            
            if show_north_arrow:
                arrow_x = bounds[0] + (bounds[2] - bounds[0]) * 0.95
                arrow_y = bounds[1] + (bounds[3] - bounds[1]) * 0.95
                ax.annotate('N', xy=(arrow_x, arrow_y), xytext=(0, -20),
                           textcoords='offset points', ha='center', va='top',
                           fontsize=14, fontweight='bold', color='black',
                           arrowprops=dict(arrowstyle='-|>', linewidth=2, color='black'))
            
            if show_colorbar:
                cbar = plt.colorbar(c, ax=ax, label=data_col, shrink=0.8)
            
            ax.set_title(f"Interpolated {data_col}", fontsize=16)
            ax.set_xlabel("Longitude", fontsize=12)
            ax.set_ylabel("Latitude", fontsize=12)
            ax.set_aspect('equal')
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Download button
            buf = io.BytesIO()
            fig.savefig(buf, format=export_format, dpi=export_dpi, bbox_inches='tight')
            buf.seek(0)
            
            st.download_button(
                label=f"📥 Download as {export_format.upper()}",
                data=buf,
                file_name=f"map.{export_format}",
                mime=f"image/{export_format}"
            )
            
            st.success("✓ Map generated!")
            plt.close(fig)

else:
    st.info("📌 Please upload CSV file and Shapefile ZIP to begin")

with st.expander("ℹ️ How to Use"):
    st.markdown("""
    **Steps:**
    1. Upload a CSV file with columns: x, y, AQI (and optionally SampleName)
    2. Upload a ZIP file containing your shapefile components
    3. Adjust settings in the sidebar
    4. Click "Generate Map"
    5. Download the result
    """)
