import streamlit as st
import requests
import pandas as pd

# ---------------------------
# GBIF Query Function
# ---------------------------
def get_gbif_occurrences(species_name, limit=500, year_range=None, bbox=None):
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        "scientificName": species_name,
        "limit": limit,
        "hasCoordinate": "true"
    }
    
    # Year filter
    if year_range:
        params["year"] = f"{year_range[0]},{year_range[1]}"
    
    # Bounding box filter
    if bbox:
        params["decimalLatitude"] = f"{bbox[0]},{bbox[1]}"
        params["decimalLongitude"] = f"{bbox[2]},{bbox[3]}"
    
    response = requests.get(url, params=params)
    data = response.json()
    
    records = []
    for result in data.get("results", []):
        if "decimalLatitude" in result and "decimalLongitude" in result:
            records.append({
                "species": result.get("scientificName"),
                "lat": result["decimalLatitude"],
                "lon": result["decimalLongitude"],
                "country": result.get("country"),
                "date": result.get("eventDate"),
                "basisOfRecord": result.get("basisOfRecord")
            })
    
    return pd.DataFrame(records)

# ---------------------------
# Streamlit App Layout
# ---------------------------
st.set_page_config(page_title="Biodiversity Informatics Tool", layout="wide")
st.title("🌍 Biodiversity Informatics Tool")
st.markdown("Search GBIF for species occurrence data and visualize results interactively.")

# Sidebar inputs
st.sidebar.header("🔎 Search Options")
species_name = st.sidebar.text_input("Species scientific name", "Danaus plexippus")
limit = st.sidebar.slider("Max records to retrieve", 100, 2000, 500, step=100)
year_range = st.sidebar.slider("Year range", 1900, 2025, (2000, 2020))

st.sidebar.subheader("Optional: Region filter (bounding box)")
lat_min = st.sidebar.number_input("Min Latitude", -90.0, 90.0, 20.0)
lat_max = st.sidebar.number_input("Max Latitude", -90.0, 90.0, 50.0)
lon_min = st.sidebar.number_input("Min Longitude", -180.0, 180.0, -130.0)
lon_max = st.sidebar.number_input("Max Longitude", -180.0, 180.0, -60.0)

bbox = (lat_min, lat_max, lon_min, lon_max) if st.sidebar.checkbox("Apply bounding box filter") else None

# Run query
if species_name:
    df = get_gbif_occurrences(species_name, limit=limit, year_range=year_range, bbox=bbox)

    if df.empty:
        st.warning("⚠️ No records found. Try changing filters or species name.")
    else:
        st.success(f"✅ Found {len(df)} records for **{species_name}**")

        # Tabs for output
        tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📋 Table", "📊 Charts"])

        with tab1:
            st.subheader("Occurrence Map")
            st.caption("Map of species records (Streamlit default)")
            st.map(df[['lat', 'lon']])

        with tab2:
            st.subheader("Occurrence Records Table")
            st.dataframe(df.head(50))
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Download full dataset as CSV",
                csv,
                f"{species_name.replace(' ', '_')}_occurrences.csv",
                "text/csv"
            )

        with tab3:
            st.subheader("Summary Statistics")

            # Records per country
            country_counts = df['country'].value_counts().reset_index()
            country_counts.columns = ["Country", "Records"]
            st.write("**Records per Country**")
            st.bar_chart(country_counts.set_index("Country"))

            # Temporal trend
            df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
            year_counts = df.dropna(subset=["year"]).groupby("year").size()

            st.write("**Records per Year**")
            st.bar_chart(year_counts)

