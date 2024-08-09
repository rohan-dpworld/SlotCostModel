import folium
import searoute as sr
from streamlit_folium import st_folium
import re


def convert_to_float(s):
    # Extract the numeric part from the string
    match = re.search(r'\(([^)]+)\)', s)
    if match:
        return float(match.group(1))
    return None
def generate_map(port_distances_df):

    run=0
    coordinates_base= None
    port_distances_df = port_distances_df.drop(index=0).reset_index(drop=True)
    port_distances_df = port_distances_df.drop(index=port_distances_df.index[-1]).reset_index(drop=True)


    for i, row in port_distances_df.iterrows():
        if run == 0:

            origin_lat= row['Origin_Lat']
            origin_lat= origin_lat[1: len(origin_lat)-1]
            origin_lat=list(origin_lat.split(','))
            origin_lat= [convert_to_float(a) for a in origin_lat]


            dest_lat = row['Destination_Lat']
            dest_lat = dest_lat[1: len(dest_lat) - 1]
            dest_lat = list(dest_lat.split(','))
            dest_lat= [convert_to_float(a) for a in dest_lat]

            route_base = sr.searoute(origin_lat, dest_lat)
            coordinates_base = route_base['geometry']['coordinates']
            run = 1
        else:
            route = sr.searoute(row['Origin_Lat'], row['Destination'])
            coordinates_base = coordinates_base + route['geometry']['coordinates']

        # Change long lat to lat long
        coordinates = [[coord[1], coord[0]] for coord in coordinates_base]

        # Create a map object
        m = folium.Map(width=500, height=400, zoom_start=8, tiles='CartoDB Positron')
        # Create a line between coordinates
        folium.PolyLine(locations=coordinates, color='black', weight=1).add_to(m)
        st_data = st_folium(m, width=725)

        return st_data

