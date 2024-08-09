## Main function
import pandas as pd
import searoute as sr


def get_fuel_consumption(filename='data/fuel_consumption.xlsx'):
    """
    Read an Excel file containing fuel consumption data for
    VLSFO and DO for varying speeds.
    """
    df = pd.read_excel(filename)
    return df


def get_port_locations(filename='data/latitude_longitude_port.xlsx'):
    """
    Read a CSV file containing latitude and longitude coordinates for ports and return a DataFrame.
    """
    df = pd.read_excel(filename)
    return df


def get_port_information(filename='data/port_information.xlsx'):
    """
    Read an Excel file containing the following information for each port code:
    port name, berth time, maneuver time, wait time, cost for TEU size
    """

    df = pd.read_excel(filename)
    df = df.fillna(method='ffill')
    df = df.drop_duplicates()
    return df


def get_port_distance(list_of_ports=None, port_locations_df=None):
    """
    Calculates port distances using latitudes and longitudes from the excel
    sheet and calls the searoute library to get distances.
    Combines all this data with the port information data, and returns 
    a dataframe with the distances and times and cost per port.

    """
    if list_of_ports is not None:
        arr = []

        for i in range(len(list_of_ports) - 1):
            origin_port_latitude = \
            port_locations_df['Latitude'][port_locations_df['Port Code'] == list_of_ports[i]].iloc[0]
            origin_port_longitude = \
            port_locations_df['Longitude'][port_locations_df['Port Code'] == list_of_ports[i]].iloc[0]
            destination_port_latitude = \
            port_locations_df['Latitude'][port_locations_df['Port Code'] == list_of_ports[i + 1]].iloc[0]
            destination_port_latitude = \
            port_locations_df['Latitude'][port_locations_df['Port Code'] == list_of_ports[i + 1]].iloc[0]
            destination_port_longitude = \
            port_locations_df['Longitude'][port_locations_df['Port Code'] == list_of_ports[i + 1]].iloc[0]
            origin = [origin_port_longitude, origin_port_latitude]
            destination = [destination_port_longitude, destination_port_latitude]
            print(origin, destination)
            route_miles = sr.searoute(origin, destination, units="mi")['properties']['length']
            arr.append([list_of_ports[i], str(origin), list_of_ports[i + 1], str(destination), route_miles])
        #Add a new row at index 0 as the Origin port
        arr.insert(0, [None, None, arr[0][0], arr[0][1], 0])
        df = pd.DataFrame(arr, columns=['Origin', 'Origin_Lat', 'Destination', 'Destination_Lat', 'Distance(Miles)'])
        return df

    return None


def collate_dataframe(port_information_df, port_distance_df, Config):
    '''
    Generates a dataframe with time and distance information for each port
    along a route.
    '''

    port_information_df= port_information_df[port_information_df['Size']==Config.Capacity]
    merged_df = port_distance_df.merge(port_information_df, left_on='Destination', right_on='Port Code', how='left')
    merged_df = merged_df[['Port Code', 'Maneuver Time', 'Wait Time', 'Berth Time', 'Port Cost', 'Distance(Miles)']]

    #The last row's values should always be zero (return to origin).
    if not merged_df.empty:
        last_row_index = merged_df.index[-1]
        merged_df.loc[last_row_index, ['Maneuver Time', 'Wait Time', 'Berth Time', 'Port Cost']] = 0

    #If any wait time, maneuver time, or berth time data is missing, fill it with averages
    merged_df['Maneuver Time'].fillna(Config.ManeuverTime, inplace=True)
    merged_df['Wait Time'].fillna(Config.WaitTime, inplace=True)
    merged_df['Berth Time'].fillna(Config.BerthTime, inplace=True)

    return merged_df


def calculate_totals(merged_df, fuel_consumption_df, Config):
    '''
    Calculates the total cost, total time, and total distance for a route.
    '''

    arr = []

    for speed in Config.Speeds:
        #For each speed, calculate sea and eca time

        arr.append([speed, None, None, None, None, None, None, None, Config.ECADistance, Config.ECADistance / speed])
        for i, row in merged_df.iterrows():
            sea_time = row['Distance(Miles)'] / speed
            arr.append([speed, row['Port Code'], sea_time, row['Maneuver Time'],
                        row['Wait Time'], row['Berth Time'], row['Port Cost'],
                        row['Distance(Miles)'], 0, 0])

    distance_and_time_df = pd.DataFrame(arr, columns=['Speed', 'Port Code',
                                                      'Sea Time', 'Maneuver Time', 'Wait Time', 'Berth Time',
                                                      'Port Cost', 'Sea Distance', 'ECA Distance', 'ECA Time'])

    time_columns = [col for col in distance_and_time_df.columns if col.endswith('Time')]
    distance_and_time_df[time_columns] = distance_and_time_df[time_columns].fillna(0)
    distance_and_time_df[time_columns] = distance_and_time_df[time_columns] / 24  #convert time to 'number of days'

    summations = distance_and_time_df.groupby(['Speed']).sum().reset_index()
    summations['Total Time'] = summations[time_columns].sum(axis=1)
    #print (summations[time_columns + ['Total Time', 'Sea Distance', 'ECA Distance']])
    summations = summations.drop(columns=['Port Code'])
    return summations


def fuel_consumption_on_sea(fuel_consumption_df, summations, Config, DO):
    """
    Returns the total VLSFO and DO consumption per day and for the entire voyage.
    """
    summations['VLSFO Fuel Consumption/day'] = summations['Speed'].apply(lambda x:
                                                                         fuel_consumption_df['Consumption'][
                                                                             (fuel_consumption_df['Speed'] == x)
                                                                             & (fuel_consumption_df['Type'] == 'FO')
                                                                             & (fuel_consumption_df[
                                                                                    'Size'] == Config.Capacity)
                                                                             ].iloc[0])
    DO_consumption = fuel_consumption_df['Consumption'][(fuel_consumption_df['Type'] == 'DO')
                                         & (fuel_consumption_df['Size'] == Config.Capacity)
                                         & (fuel_consumption_df['Speed'] == DO.Speed)
                                         ].iloc[0]
    summations['DO Fuel Consumption/day'] = DO_consumption
    summations['DO Fuel Consumption'] = summations['DO Fuel Consumption/day'] * summations['ECA Time']
    summations['VLSFO Fuel Consumption'] = summations['VLSFO Fuel Consumption/day'] * (summations['Sea Time'] - summations['ECA Time'] )

    return summations

def voyage_consumption(summations, DO, FO):

    summations['Maneuver Fuel Consumption/day']=FO.ManeuverConsumptionPerDay
    summations['Berth Fuel Consumption/day']=DO.BerthConsumptionPerDay
    summations['Maneuver Fuel Consumption']= summations['Maneuver Fuel Consumption/day']* summations['Maneuver Time']
    summations['Berth Fuel Consumption'] = summations['Berth Fuel Consumption/day'] * summations['Berth Time']

    return summations


def bunker_consumption(summations, DO, FO):
    summations['VLSFO Bunker Cost'] = (summations['VLSFO Fuel Consumption'] + summations['Maneuver Fuel Consumption'] ) * FO.BunkerPrice
    summations['DO Bunker Cost'] = (summations['DO Fuel Consumption'] + summations['Berth Fuel Consumption']) * DO.BunkerPrice
    return summations

def total_costs(summations, Costs, Config):

    charter_hires= Config.CharterHires
    arr=[]

    for i, row in summations.iterrows():
        for charter_hire in charter_hires:
            charter_cost= row['Total Time'] * charter_hire
            agency_cost= Costs.Agency
            miscellaneous_cost= Costs.Miscellaneous

            new_row = row.to_dict()
            new_row['Charter Cost'] = charter_cost
            new_row['Agency Cost'] = agency_cost
            new_row['Miscellaneous Cost'] = miscellaneous_cost
            new_row['Charter Hire']= charter_hire
            arr.append(new_row)

    total_costs_df = pd.DataFrame(arr)
    cost_columns = [col for col in total_costs_df.columns if col.endswith('Cost')]
    total_costs_df['Total Cost'] = total_costs_df[cost_columns].sum(axis=1)

    return total_costs_df

def summary_table(total_costs_df, Config):

    arr=[]

    for i, old_row in total_costs_df.iterrows():
        # Calculate total voyage cost, slot cost, annual voyage cost, and voyage market revenue
        row = old_row.to_dict()
        row['Total Voyage Cost'] = (row['Total Time'] * row['Charter Hire']) + (row['Total Cost'] - row['Charter Cost'])
        row['Slot Cost'] = row['Total Voyage Cost'] / (Config.Capacity * Config.TEUPercent)
        row['Annual Voyage Cost'] = row['Total Voyage Cost'] * 365 / row['Total Time']
        row['Voyage Market Revenue'] = Config.SlotRevenue * (Config.Capacity * Config.TEUPercent)
        row['Annual Market Revenue'] = row['Voyage Market Revenue'] * 365 / row['Total Time']
        arr.append(row)

    total_costs_df = pd.DataFrame(arr)

    return total_costs_df
