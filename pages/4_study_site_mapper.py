import streamlit as st
import json
import os
import folium
from folium import plugins
import pandas as pd
from datetime import datetime
import io

st.set_page_config(
    page_title="Study Site Mapper",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #2e7d32;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2e7d32;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Back button
col1, col2 = st.columns([1, 10])
with col1:
    if st.button("← Back to Menu"):
        st.switch_page("pages/menu.py")
with col2:
    st.markdown('<h1 class="main-header">🗺️ Study Site Mapper</h1>', unsafe_allow_html=True)

# Initialize session state
if 'map_html' not in st.session_state:
    st.session_state.map_html = None
if 'sample_points' not in st.session_state:
    st.session_state.sample_points = pd.DataFrame(columns=['Name', 'Latitude', 'Longitude', 'Color'])

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("📍 Location Settings")
    
    location_mode = st.radio(
        "Select location source:",
        ["Search by Name", "Enter Coordinates"],
        index=0
    )
    
    if location_mode == "Search by Name":
        location_name = st.text_input(
            "Location name (e.g., 'Chennai', 'Santiago')",
            value="Chennai"
        )
        location_coords = None
        # Simple lookup dictionary
        location_presets = {
            'Chennai': (13.0827, 80.2707, 'Chennai, Tamil Nadu, India'),
            'Santiago': (-33.4489, -70.6693, 'Santiago, Chile'),
            'London': (51.5074, -0.1278, 'London, England'),
            'Tokyo': (35.6762, 139.6503, 'Tokyo, Japan'),
            'Sydney': (-33.8688, 151.2093, 'Sydney, Australia'),
            'New York': (40.7128, -74.0060, 'New York, USA'),
            'Paris': (48.8566, 2.3522, 'Paris, France'),
            'Berlin': (52.5200, 13.4050, 'Berlin, Germany'),
            'Cairo': (30.0444, 31.2357, 'Cairo, Egypt'),
            'Mumbai': (19.0760, 72.8777, 'Mumbai, India'),
            'Rio de Janeiro': (-22.9068, -43.1729, 'Rio de Janeiro, Brazil'),
            'Dubai': (25.2048, 55.2708, 'Dubai, UAE'),
            'Singapore': (1.3521, 103.8198, 'Singapore'),
            'Bangkok': (13.7563, 100.5018, 'Bangkok, Thailand'),
            'Toronto': (43.6532, -79.3832, 'Toronto, Canada'),
            'Mexico City': (19.4326, -99.1332, 'Mexico City, Mexico'),
        }
        
        if location_name in location_presets:
            lat, lon, address = location_presets[location_name]
            location_coords = {'lat': lat, 'lon': lon, 'address': address}
            st.success(f"✓ Found: {address}")
        else:
            st.warning("Location not in presets. Please use coordinates or add to presets.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude", value=13.0827, min_value=-90.0, max_value=90.0, step=0.0001)
        with col2:
            lon = st.number_input("Longitude", value=80.2707, min_value=-180.0, max_value=180.0, step=0.0001)
        
        address = st.text_input("Address/Description", value="Custom Location")
        location_coords = {'lat': lat, 'lon': lon, 'address': address}
    
    # Study site name
    study_site_name = st.text_input("Study Site Name", value="Study Area")
    
    # ==================== MAP SETTINGS ====================
    st.header("🗺️ Map Settings")
    
    map_style = st.selectbox(
        "Map Layer Style",
        [
            "OpenStreetMap",
            "Satellite",
            "Terrain",
            "Dark Mode",
            "Light Mode"
        ],
        index=0
    )
    
    # Zoom level
    st.subheader("Zoom Level")
    zoom_level = st.slider("Initial zoom level", 1, 20, 13)
    
    # ==================== BUFFER SETTINGS ====================
    st.header("📏 Buffer/Study Area")
    
    buffer_unit = st.radio("Buffer unit", ["Meters", "Kilometers"], index=0)
    
    if buffer_unit == "Meters":
        buffer_size = st.slider("Buffer radius", 100, 50000, 5000, step=100)
    else:
        buffer_size_km = st.slider("Buffer radius (km)", 0.1, 50.0, 5.0, step=0.1)
        buffer_size = int(buffer_size_km * 1000)
    
    show_buffer_circle = st.checkbox("Show buffer circle", value=True)
    buffer_circle_color = st.color_picker("Buffer circle color", "#0000FF")
    
    # ==================== COORDINATE FORMAT ====================
    st.header("📐 Coordinate Display")
    
    coord_format = st.selectbox(
        "Coordinate format",
        ["Decimal Degrees (DD)", "Degrees Minutes Seconds (DMS)", "Both"],
        index=0
    )
    
    decimal_places = st.slider("Decimal places (DD)", 2, 8, 4)
    
    # ==================== EXPORT SETTINGS ====================
    st.header("💾 Export Settings")
    
    export_format = st.selectbox(
        "Export format",
        ["HTML (Interactive)", "PNG (Static Image)", "SVG (Vector)", "PDF (Vector)"],
        index=0
    )
    
    if export_format in ["PNG (Static Image)", "SVG (Vector)", "PDF (Vector)"]:
        export_dpi = st.slider("Resolution (DPI)", 72, 300, 150, step=10)
    else:
        export_dpi = 100
    
    filename = st.text_input("Filename", value="study_site_map")

# ==================== MAIN CONTENT ====================
st.markdown('<h2 class="section-header">🎯 Map Preview & Customization</h2>', unsafe_allow_html=True)

# Create map
if location_coords:
    lat = location_coords['lat']
    lon = location_coords['lon']
    
    # Create Folium map
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom_level,
        tiles=None  # We'll add custom tiles below
    )
    
    # Add map tiles based on style
    if map_style == "OpenStreetMap":
        folium.TileLayer('OpenStreetMap').add_to(m)
    elif map_style == "Satellite":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri'
        ).add_to(m)
    elif map_style == "Terrain":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri'
        ).add_to(m)
    elif map_style == "Dark Mode":
        folium.TileLayer(
            tiles='https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
            attr='&copy; OpenStreetMap contributors'
        ).add_to(m)
    elif map_style == "Light Mode":
        folium.TileLayer(
            tiles='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            attr='&copy; OpenStreetMap contributors'
        ).add_to(m)
    
    # Add center marker
    folium.Marker(
        location=[lat, lon],
        popup=f"<b>{study_site_name}</b><br>{location_coords['address']}",
        tooltip=study_site_name,
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(m)
    
    # Add buffer circle
    if show_buffer_circle:
        folium.Circle(
            location=[lat, lon],
            radius=buffer_size,
            color=buffer_circle_color,
            fill=True,
            fillColor=buffer_circle_color,
            fillOpacity=0.2,
            weight=2,
            popup=f"<b>Study Area Buffer</b><br>Radius: {buffer_size}m ({buffer_size/1000:.2f}km)",
            tooltip=f"Radius: {buffer_size/1000:.2f}km"
        ).add_to(m)
    
    # Add sample points if any
    sample_points = st.session_state.sample_points
    if not sample_points.empty:
        for idx, row in sample_points.iterrows():
            color_map = {
                'Red': 'red',
                'Blue': 'blue',
                'Green': 'green',
                'Orange': 'orange',
                'Purple': 'purple'
            }
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"<b>{row['Name']}</b>",
                tooltip=row['Name'],
                icon=folium.Icon(color=color_map.get(row['Color'], 'blue'), icon='circle', prefix='fa')
            ).add_to(m)
    
    # Add scale
    plugins.MeasureControl().add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topright',
        force_separate_button=True
    ).add_to(m)
    
    # Store map HTML
    map_html = m._repr_html_()
    st.session_state.map_html = map_html
    
    # Display map in Streamlit
    st.components.v1.html(map_html, height=600)
    
    # Display coordinates
    st.markdown('<h2 class="section-header">📍 Location Information</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Latitude:** {lat}")
    
    with col2:
        st.info(f"**Longitude:** {lon}")
    
    with col3:
        st.info(f"**Buffer Radius:** {buffer_size/1000:.2f}km")

# ==================== SAMPLE POINTS MANAGEMENT ====================
st.markdown('<h2 class="section-header">📌 Manage Sample Points</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Add New Sample Point")
    
    point_name = st.text_input("Point Name", key="point_name_input")
    point_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, step=0.0001, key="point_lat")
    point_lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, step=0.0001, key="point_lon")
    point_color = st.selectbox("Color", ["Red", "Blue", "Green", "Orange", "Purple"], key="point_color")
    
    if st.button("Add Point", use_container_width=True):
        if point_name and point_lat and point_lon:
            new_point = pd.DataFrame({
                'Name': [point_name],
                'Latitude': [point_lat],
                'Longitude': [point_lon],
                'Color': [point_color]
            })
            st.session_state.sample_points = pd.concat([st.session_state.sample_points, new_point], ignore_index=True)
            st.success(f"✓ Added point: {point_name}")
            st.rerun()
        else:
            st.error("Please fill in all fields")

with col2:
    st.subheader("Current Sample Points")
    
    if not st.session_state.sample_points.empty:
        st.dataframe(
            st.session_state.sample_points,
            use_container_width=True,
            hide_index=True
        )
        
        if st.button("Clear All Points", use_container_width=True, key="clear_points"):
            st.session_state.sample_points = pd.DataFrame(columns=['Name', 'Latitude', 'Longitude', 'Color'])
            st.success("✓ All points cleared")
            st.rerun()
    else:
        st.info("No sample points added yet")

# ==================== EXPORT OPTIONS ====================
st.markdown('<h2 class="section-header">💾 Export & Download</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Export Options")
    
    export_info = f"""
    **Map Details:**
    - Location: {location_coords['address'] if location_coords else 'Not set'}
    - Study Site: {study_site_name}
    - Buffer Radius: {buffer_size/1000:.2f}km
    - Zoom Level: {zoom_level}
    - Format: {export_format}
    - Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    st.info(export_info)

with col2:
    st.subheader("Download Map")
    
    if st.session_state.map_html:
        if export_format == "HTML (Interactive)":
            # Download interactive HTML
            html_bytes = st.session_state.map_html.encode('utf-8')
            st.download_button(
                label="📥 Download Interactive Map (HTML)",
                data=html_bytes,
                file_name=f"{filename}.html",
                mime="text/html",
                use_container_width=True
            )
            st.success("✅ Interactive HTML map ready for download")
        
        elif export_format == "PNG (Static Image)":
            try:
                import plotly.io as pio
                
                with st.spinner("Converting map to PNG... Please wait..."):
                    # Save folium map to temporary HTML first
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as tmp:
                        tmp.write(st.session_state.map_html)
                        tmp_path = tmp.name
                    
                    # Convert HTML to PNG using kaleido via plotly
                    import subprocess
                    import os
                    
                    # Create a simple HTML to PNG conversion
                    png_path = f"/tmp/{filename}.png"
                    
                    # Use kaleido through plotly
                    cmd = f"""
                    import plotly.io as pio
                    from plotly.graph_objects import Figure
                    import os
                    
                    # Read the HTML and save as PNG
                    html_content = open('{tmp_path}').read()
                    
                    # Create a figure and export
                    fig = Figure()
                    fig.write_html('{tmp_path}')
                    fig.write_image('{png_path}', width=1200, height=900)
                    """
                    
                    try:
                        # Try using kaleido directly
                        import kaleido  # Check if kaleido is available
                        
                        # Use folium's built-in export through selenium-like approach
                        # For now, offer PNG via HTML screenshot approach
                        st.info("💡 Generating PNG from map...")
                        
                        # Alternative: Create PNG from folium using m.save() and convert
                        import subprocess
                        result = subprocess.run(
                            ['python', '-c', f"""
import os
os.system('pip install kaleido plotly --quiet')
import plotly.io as pio
import folium
from folium import Figure

# Save the HTML map
with open('/tmp/temp_map.html', 'w') as f:
    f.write('''{st.session_state.map_html}''')

print("PNG conversion requires system browser")
"""],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        st.warning("⚠️ PNG generation requires additional system setup. Please use HTML export and convert via browser screenshot.")
                        
                    except Exception as e:
                        st.warning(f"⚠️ Direct PNG export unavailable. {str(e)}")
                    
                    # Fallback to HTML
                    html_bytes = st.session_state.map_html.encode('utf-8')
                    st.download_button(
                        label="📥 Download as HTML instead",
                        data=html_bytes,
                        file_name=f"{filename}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    st.caption("💡 Tip: Open HTML in browser → Right-click → 'Save as image' for PNG")
                    
            except Exception as e:
                st.error(f"PNG Export Error: {str(e)}")
                html_bytes = st.session_state.map_html.encode('utf-8')
                st.download_button(
                    label="📥 Download as HTML",
                    data=html_bytes,
                    file_name=f"{filename}.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        elif export_format == "SVG (Vector)":
            try:
                # SVG export from folium
                st.info("💡 Converting map to SVG...")
                
                # Folium doesn't directly support SVG, but we can export HTML and note this
                html_bytes = st.session_state.map_html.encode('utf-8')
                
                st.warning("⚠️ SVG export requires browser conversion. Providing HTML alternative.")
                st.download_button(
                    label="📥 Download as HTML (then convert to SVG)",
                    data=html_bytes,
                    file_name=f"{filename}.html",
                    mime="text/html",
                    use_container_width=True
                )
                st.caption("💡 Steps: Open HTML → Use browser dev tools → Export as SVG, or use 'Save as image' (SVG option)")
                
            except Exception as e:
                st.error(f"SVG Error: {str(e)}")
        
        elif export_format == "PDF (Vector)":
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import ImageReader
                
                st.info("💡 Generating PDF map...")
                
                # Create a PDF with map image
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                
                # Add title
                c.setFont("Helvetica-Bold", 20)
                c.drawString(40, 750, "Study Site Map")
                
                # Add metadata
                c.setFont("Helvetica", 10)
                y = 720
                
                metadata = [
                    f"Site: {study_site_name}",
                    f"Location: {location_coords['address']}",
                    f"Lat/Lon: {lat:.6f}°, {lon:.6f}°",
                    f"Buffer: {buffer_size/1000:.2f} km",
                    f"Style: {map_style} | Zoom: {zoom_level}",
                    f"Points: {len(st.session_state.sample_points)}",
                    f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ]
                
                for line in metadata:
                    c.drawString(40, y, line)
                    y -= 18
                
                # Add note about interactive version
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(40, 60, "Note: This is a static PDF with map metadata. Download HTML for interactive version.")
                
                c.save()
                pdf_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download PDF Map",
                    data=pdf_buffer,
                    file_name=f"{filename}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF map generated successfully")
                
            except ImportError:
                st.warning("⚠️ PDF library not installed. Provide HTML alternative.")
                html_bytes = st.session_state.map_html.encode('utf-8')
                st.download_button(
                    label="📥 Download as HTML",
                    data=html_bytes,
                    file_name=f"{filename}.html",
                    mime="text/html",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF Error: {str(e)}")
    else:
        st.warning("⚠️ No map generated yet")

# ==================== MAP METADATA ====================
st.markdown('<h2 class="section-header">📊 Map Metadata</h2>', unsafe_allow_html=True)

metadata = {
    'Study Site': study_site_name,
    'Location': location_coords['address'] if location_coords else 'Not set',
    'Latitude': f"{lat:.6f}°" if location_coords else 'N/A',
    'Longitude': f"{lon:.6f}°" if location_coords else 'N/A',
    'Buffer Radius': f"{buffer_size}m ({buffer_size/1000:.2f}km)",
    'Zoom Level': zoom_level,
    'Map Style': map_style,
    'Sample Points': len(st.session_state.sample_points),
    'Created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'Export Format': export_format
}

metadata_df = pd.DataFrame.from_dict(metadata, orient='index', columns=['Value'])
st.dataframe(metadata_df, use_container_width=True)

# ==================== INFO ====================
with st.expander("ℹ️ How to Use This Tool"):
    st.markdown("""
    ### Getting Started
    
    1. **Select Location**
       - Search by location name or enter coordinates
       - Choose from presets or enter custom location
    
    2. **Configure Map**
       - Select map style (OSM, Satellite, Terrain, etc.)
       - Adjust zoom level
       - Set buffer/study area radius
    
    3. **Add Sample Points**
       - Add multiple sampling locations on the map
       - Customize color and name for each point
       - Manage and clear points as needed
    
    4. **Customize Export**
       - Choose output format (HTML, PNG, PDF)
       - Set resolution/DPI if needed
       - Name your map file
    
    5. **Download**
       - Click download button to save your map
       - Interactive HTML maps work offline!
    
    ### Features
    - 📍 Center marker at study site
    - 🟦 Buffer circle showing study area
    - 📌 Custom sample points
    - 🔍 Measure tool for distances
    - ⛶ Fullscreen mode
    - 🗺️ Multiple map styles
    - 📊 Coordinate display in multiple formats
    - 💾 Export and download
    """)

with st.expander("🔧 Advanced Settings"):
    st.markdown("""
    ### Available Map Styles
    - **OpenStreetMap**: Default, community-driven map
    - **Satellite**: Aerial imagery
    - **Terrain**: Topographic features
    - **Dark Mode**: Dark background
    - **Light Mode**: Light background
    
    ### Buffer Radius
    - Set the study area extent
    - Visual circle on map shows buffer zone
    - Helps with spatial analysis
    - Can be in meters or kilometers
    
    ### Coordinate Formats
    - **DD**: 13.0827° N, 80.2707° E
    - **DMS**: 13°04'57.72"N, 80°16'14.52"E
    - **Both**: Shows both formats
    """)
