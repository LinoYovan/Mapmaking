import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from scipy.interpolate import Rbf
from matplotlib.gridspec import GridSpec
from datetime import datetime
import tempfile
import zipfile
import os
import io

# Set page configuration
st.set_page_config(
    page_title="Multi-Map Grid Generator",
    page_icon="📊",
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

# Back button
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("← Back to Menu"):
        st.switch_page("pages/menu.py")
with col2:
    st.markdown('<h1 class="main-header">📊 Multi-Map Grid Generator</h1>', unsafe_allow_html=True)

# Initialize session state
if 'gdf_boundary' not in st.session_state:
    st.session_state.gdf_boundary = None
if 'gdf_points' not in st.session_state:
    st.session_state.gdf_points = None

# Sidebar for inputs
with st.sidebar:
    st.header("📤 Upload Data")
    csv_file = st.file_uploader("Upload CSV File", type=['csv'])
    
    st.subheader("Shapefile Upload")
    shapefile_zip = st.file_uploader(
        "Upload Shapefile ZIP",
        type=['zip'],
        help="Upload a ZIP file containing all shapefile components"
    )
    
    st.header("⚙️ Column Settings")
    x_col = st.text_input("X Coordinate Column", "x")
    y_col = st.text_input("Y Coordinate Column", "y")
    data_col = st.text_input("Data Column", "AQI")
    date_col = st.text_input("Date Column", "Date")
    
    st.header("🎨 Interpolation")
    interpolation_resolution = st.slider("Resolution", 100, 500, 300)
    rbf_function = st.selectbox(
        "RBF Function",
        ['multiquadric', 'inverse', 'gaussian', 'linear', 'cubic', 'quintic', 'thin_plate'],
        index=2
    )
    rbf_smooth = st.slider("Smoothing", 0.0, 1.0, 0.1)
    
    st.header("📐 Layout")
    plot_columns = st.slider("Columns in Grid", 2, 12, 6)
    figure_width = st.slider("Figure Width (inches)", 10, 40, 20)
    figure_height = st.slider("Figure Height (inches)", 8, 30, 15)
    
    st.header("🖼️ Map Elements")
    show_points = st.checkbox("Show Sample Points", True)
    show_colorbar = st.checkbox("Show Colorbar", True)
    show_scalebar = st.checkbox("Show Scalebar", True)
    show_north_arrow = st.checkbox("Show North Arrow", True)
    show_labels = st.checkbox("Show Point Labels", False)
    show_legend = st.checkbox("Show Legend", True)
    
    st.header("🎨 Colors & Style")
    colormap = st.selectbox(
        "Colormap",
        plt.colormaps(),
        index=plt.colormaps().index('inferno') if 'inferno' in plt.colormaps() else 0
    )
    contour_levels = st.slider("Contour Levels", 5, 50, 20)
    
    st.header("💾 Save Settings")
    save_map = st.checkbox("Save Map", True)
    save_format = st.selectbox("Format", ['png', 'pdf', 'svg', 'jpg', 'tiff'])
    save_dpi = st.slider("DPI (for raster formats)", 100, 300, 300)

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

def perform_interpolation(points_df, xi, yi, inside_mask, data_column, rbf_func, rbf_smooth):
    xi_inside = xi[inside_mask]
    yi_inside = yi[inside_mask]
    
    rbf = Rbf(points_df[x_col], points_df[y_col], points_df[data_column], 
              function=rbf_func, smooth=rbf_smooth)
    zi_rbf = rbf(xi_inside, yi_inside)
    
    zi_full = np.full_like(xi, np.nan)
    zi_full[inside_mask] = zi_rbf
    
    return np.ma.masked_where(~inside_mask, zi_full)

def plot_map(ax, gdf_boundary, gdf_points, xi, yi, zi_masked, title_text):
    gdf_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
    
    if colormap not in plt.colormaps():
        cmap = 'viridis'
    else:
        cmap = colormap
    
    c = ax.contourf(xi, yi, zi_masked, levels=contour_levels, cmap=cmap, alpha=0.75)
    
    if show_points:
        gdf_points.plot(ax=ax, color='blue', markersize=50, marker='o', 
                       edgecolor='black', linewidth=1)
    
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
                f'{scalebar_length/1000:.0f} km', ha='center', va='top', fontsize=10)
    
    if show_north_arrow:
        bounds = gdf_boundary.total_bounds
        arrow_x = bounds[0] + (bounds[2] - bounds[0]) * 0.95
        arrow_y = bounds[1] + (bounds[3] - bounds[1]) * 0.95
        
        ax.annotate('N', xy=(arrow_x, arrow_y), xytext=(0, -20), 
                   textcoords='offset points', ha='center', va='top', 
                   fontsize=14, fontweight='bold', color='black',
                   arrowprops=dict(arrowstyle='-|>', linewidth=2, color='black'))
    
    ax.set_title(title_text, fontsize=12)
    ax.set_xticks([])
    ax.set_yticks([])
    
    return c

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
                return None
        else:
            st.error("No .shp file found in the uploaded ZIP archive")
            return None

# Process files
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
        shapefile_loaded = True

# Main visualization
if shapefile_loaded and st.session_state.gdf_boundary is not None:
    st.markdown('<h2 class="section-header">📊 Generate Maps</h2>', unsafe_allow_html=True)
    
    xi, yi, inside_mask = create_interpolation_grid(
        st.session_state.gdf_boundary, 
        interpolation_resolution
    )
    
    grouped = st.session_state.gdf_points.groupby(['year', 'month'])
    num_plots = len(grouped)
    
    st.info(f"📌 Found {num_plots} time periods. Creating {plot_columns} columns × {int(np.ceil(num_plots/plot_columns))} rows")
    
    if st.button("🎨 Generate Static Maps"):
        with st.spinner("Generating maps..."):
            # Create figure layout
            plot_rows = int(np.ceil(num_plots / plot_columns))
            fig = plt.figure(figsize=(figure_width, figure_height), dpi=100)
            gs = GridSpec(plot_rows, plot_columns, hspace=0.3, wspace=0.3)
            
            progress_bar = st.progress(0)
            
            vmin = st.session_state.gdf_points[data_col].min()
            vmax = st.session_state.gdf_points[data_col].max()
            
            for i, ((year, month), month_df) in enumerate(grouped):
                row = i // plot_columns
                col = i % plot_columns
                
                month_gdf = st.session_state.gdf_points[
                    (st.session_state.gdf_points['month'] == month) & 
                    (st.session_state.gdf_points['year'] == year)
                ]
                
                zi_masked = perform_interpolation(
                    month_df, xi, yi, inside_mask, data_col, 
                    rbf_function, rbf_smooth
                )
                
                ax = fig.add_subplot(gs[row, col])
                
                title_text = datetime(year, month, 1).strftime('%B %Y')
                plot_map(ax, st.session_state.gdf_boundary, month_gdf, xi, yi, zi_masked, title_text)
                
                progress_bar.progress((i + 1) / num_plots)
            
            fig.suptitle(f"{data_col} Distribution (2023-2024)", fontsize=16, y=0.98)
            plt.tight_layout()
            
            # Display in streamlit
            st.pyplot(fig)
            
            # Download button
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=save_dpi, bbox_inches='tight')
            buf.seek(0)
            
            st.download_button(
                label=f"📥 Download as {save_format.upper()}",
                data=buf,
                file_name=f"aqi_maps.{save_format}",
                mime=f"image/{save_format}"
            )
            
            st.success("✓ Maps generated successfully!")
            
            plt.close(fig)

else:
    st.info("📌 Please upload CSV file and Shapefile ZIP to begin")

# Help section
with st.expander("ℹ️ How to Use", expanded=False):
    st.markdown("""
    **Steps:**
    1. Upload your CSV and Shapefile ZIP
    2. Adjust layout and style settings
    3. Click 'Generate Static Maps'
    4. Download the result
    
    **Tips:**
    - Grid layout shows all months at once
    - Adjust spacing and DPI for final output
    - Higher DPI = better quality but slower rendering
    """)
