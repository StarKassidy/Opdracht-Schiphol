import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set the page layout to wide
st.set_page_config(layout="wide")

# Add a title
st.title("Aircraft Data Visualizations")

# Create tabs for different sections
tabs = st.tabs(["Plane Tracks and Sensor Data", 
                "Plane Manufacturers and Sound Levels", 
                "Correlation between Passengers, Weight, and Sound"])

# Content for the "Plane Tracks and Sensor Data" Tab
with tabs[0]:
    st.header("Visualization of Plane Tracks and Sensor Data")
    st.write("""
        This tab visualizes the flight paths of two planes and shows which sensors in Kudelstaartseweg 
        picked up their sound. The tracks are displayed on a map, and we can also analyze 
        the locations of the sensors and how they relate to the planes' paths.
    """)
    # Insert your plane track and sensor sound visualization code here

# Content for the "Plane Manufacturers and Sound Levels" Tab
with tabs[1]:
    st.header("Plane Manufacturers and Their Sound Levels")
    st.write("""
        In this tab, we explore the sound levels of various plane manufacturers and 
        how their aircraft compare in terms of loudness. You can visualize the sound levels 
        based on the manufacturer's data.
    """)
    # Insert your code to visualize plane manufacturers and sound levels here

# Content for the "Correlation between Passengers, Weight, and Sound" Tab
with tabs[2]:
    st.header("Correlation between Passengers, Weight, and Sound")
    st.write("""
        This tab examines the relationship between the number of passengers, the plane's 
        weight, and the sound it produces. It offers insights into how these factors might 
        be correlated.
    """)

    # Fetch data function
    @st.cache_data
    def fetch_data():
        url = 'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D=1735689600&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D=1742774400'
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            if response.status_code == 200:
                colnames = pd.DataFrame(response.json()['metadata'])
                data = pd.DataFrame(response.json()['rows'])
                data.columns = colnames.headers
                data['time'] = pd.to_datetime(data['time'], unit='s')
                return data
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    # Mock data function
    def get_mock_data():
        data = pd.DataFrame({
            'time': pd.date_range(start="2025-01-01", periods=10, freq='D'),
            'vliegtuig_type': ['Boeing 737-800', 'Embraer ERJ 170-200 STD', 'Embraer ERJ 190-100 STD', 
                               'Boeing 737-700', 'Airbus A320 214', 'Boeing 777-300ER', 
                               'Boeing 737-900', 'Boeing 777-200', 'Airbus A319-111', 'Boeing 787-9'],
            'SEL_dB': [85, 90, 95, 100, 92, 88, 91, 96, 99, 93],
        })
        return data

    # Function to calculate noise per passenger and cargo
    @st.cache_data
    def calculate_noise_per_passenger_and_cargo(data, aircraft_capacity, load_factor):
        results = []
        for _, row in data.iterrows():
            aircraft_type = row['vliegtuig_type']
            if aircraft_type in aircraft_capacity:
                sel_dB = row['SEL_dB']
                passengers = aircraft_capacity[aircraft_type]['passengers']
                cargo_ton = aircraft_capacity[aircraft_type]['cargo_ton']
                
                occupied_passengers = passengers * load_factor
                noise_per_passenger = sel_dB / occupied_passengers if occupied_passengers != 0 else np.nan
                noise_per_cargo = sel_dB / cargo_ton if cargo_ton != 0 else np.nan
                
                results.append({
                    'aircraft_type': aircraft_type,
                    'passengers': passengers,
                    'noise_per_passenger': noise_per_passenger,
                    'noise_per_cargo': noise_per_cargo
                })

        return pd.DataFrame(results)

    # Aircraft capacity data
    aircraft_capacity = {
        'Boeing 737-800': {'passengers': 189, 'cargo_ton': 20},
        'Embraer ERJ 170-200 STD': {'passengers': 80, 'cargo_ton': 7},
        'Embraer ERJ 190-100 STD': {'passengers': 98, 'cargo_ton': 8},
        'Boeing 737-700': {'passengers': 130, 'cargo_ton': 17},
        'Airbus A320 214': {'passengers': 180, 'cargo_ton': 20},
        'Boeing 777-300ER': {'passengers': 396, 'cargo_ton': 60},
        'Boeing 737-900': {'passengers': 220, 'cargo_ton': 25},
        'Boeing 777-200': {'passengers': 314, 'cargo_ton': 50},
        'Airbus A319-111': {'passengers': 156, 'cargo_ton': 16},
        'Boeing 787-9': {'passengers': 296, 'cargo_ton': 45}
    }

    # Load factor
    load_factor = 0.85

    # Get data
    data = fetch_data()
    if data is None:
        data = get_mock_data()

    # Perform calculations
    results = calculate_noise_per_passenger_and_cargo(data, aircraft_capacity, load_factor)

    # Sort results
    sorted_results_passenger = results.sort_values(by='noise_per_passenger')
    sorted_results_cargo = results.sort_values(by='noise_per_cargo')

    # Create plots
    st.subheader('Top 10 Aircraft Types - Noise per Passenger & Cargo')

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sns.barplot(x='aircraft_type', y='noise_per_passenger', data=sorted_results_passenger, palette='viridis', ax=axes[0])
    axes[0].set_title('Noise per Passenger per Aircraft Type', fontsize=14)
    axes[0].set_xlabel('Aircraft Type', fontsize=12)
    axes[0].set_ylabel('Noise per Passenger (dB)', fontsize=12)
    axes[0].tick_params(axis='x', rotation=45)

    sns.barplot(x='aircraft_type', y='noise_per_cargo', data=sorted_results_cargo, palette='viridis', ax=axes[1])
    axes[1].set_title('Noise per Ton Cargo per Aircraft Type', fontsize=14)
    axes[1].set_xlabel('Aircraft Type', fontsize=12)
    axes[1].set_ylabel('Noise per Cargo (dB)', fontsize=12)
    axes[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    st.pyplot(fig)

    # Categorize by passenger count
    st.subheader('Noise Comparison by Passenger Category')
    def categorize_by_passenger_count(passenger_count):
        if passenger_count <= 100:
            return '0-100 Passengers'
        elif 101 <= passenger_count <= 150:
            return '101-150 Passengers'
        elif 151 <= passenger_count <= 200:
            return '151-200 Passengers'
        else:
            return '201+ Passengers'

    results['passenger_category'] = results['passengers'].apply(categorize_by_passenger_count)

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='passenger_category', y='noise_per_passenger', data=results, palette='Set2')
    plt.title('Noise per Passenger by Category', fontsize=16)
    plt.xlabel('Passenger Category', fontsize=12)
    plt.ylabel('Noise per Passenger (dB)', fontsize=12)
    plt.xticks(rotation=45)

    st.pyplot(plt)
