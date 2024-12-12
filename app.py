import folium
import streamlit as st
from geopy.geocoders import Nominatim

from streamlit_folium import st_folium

# Initialize geocoder with a more descriptive user agent
geolocator = Nominatim(user_agent="my_unique_app_name")  # Change to a unique name

# Add a text input for user location
user_location = st.text_input("Enter a location:", "Kaohsiung")  # Default to Kaohsiung

# Get latitude and longitude from user input
if user_location:
    location = geolocator.geocode(user_location)
    if location:
        latitude, longitude = location.latitude, location.longitude
    else:
        st.error("Location not found. Please try another one.")
else:
    latitude, longitude = 39.949610, -75.150282  # Default to Liberty Bell coordinates

# Update map with user location
m = folium.Map(location=[latitude, longitude], zoom_start=16)
folium.Marker(
    [latitude, longitude], popup=user_location, tooltip=user_location
).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)