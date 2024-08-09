#This page contains all the streamlit functions to display information.
#they will call other functions that perform calculations internally.
#This is the main entry point for all display.

import streamlit as st
import config as cfg
import calculate
import trace_map


def initialize_session_states(exclusion_list=[]):
    if 'dropdowns' not in st.session_state:
        st.session_state['dropdowns'] = [0]
    if 'selected_paths' not in st.session_state:
        st.session_state['selected_paths'] = []
    if 'done_clicked' not in st.session_state:
        st.session_state['done_clicked'] = False


def render_dropdowns(port_codes):
    dropdowns = st.session_state['dropdowns']
    selected_paths = []

    for i in range(len(dropdowns)):
        selected_path = st.selectbox(f'Select Port Code {i + 1}', port_codes, key=f'dropdown_{i}')
        selected_paths.append(selected_path)

    return selected_paths


def render_recursive_dropdowns(port_codes):
    selected_paths = render_dropdowns(port_codes)

    col1, col2, col3, col4 = st.columns(4)

    # Button to add more dropdowns
    if col1.button('Add Path'):
        st.session_state['dropdowns'].append(len(st.session_state['dropdowns']))

    # Button to cancel
    if col3.button('Refresh Path'):
        initialize_session_states()

    # Button to finalize selections
    if col2.button('Done'):
        st.write('Selected Paths:', selected_paths)
        st.session_state['selected_paths'] = selected_paths
        st.session_state['done_clicked'] = True

    # Button to remove the last dropdown
    if col4.button('Remove Last Port'):
        if len(st.session_state['dropdowns']) > 1:  # Ensure at least one dropdown remains
            st.session_state['dropdowns'].pop()

    #st.write('Current State:', st.session_state)


def display() -> None:
    #Initializations and getting necessary data

    initialize_session_states()

    port_information_df = calculate.get_port_information()
    port_locations_df = calculate.get_port_locations()
    fuel_consumption_df = calculate.get_fuel_consumption()

    st.title(":blue[Slot Cost Application]")

    st.markdown('**Enter Vessel Configurations**')

    col11, col12= st.columns(2)
    capacity = col11.selectbox('Enter Capacity (in TEUs)', (2500, 8000, 10000, 15000, 20000, 24000))
    forty_feet_container_percent = col12.number_input('Enter percentage of 40 ft. containers (between 0 and 100)')

    col21, col22 = st.columns(2)
    eca_distance = col21.number_input('Enter ECA distance (in miles)')
    frequency = col22.number_input('Enter frequency of vessels')

    col31, col32= st.columns(2)
    teu_capacity= col31.number_input('Enter volume of vessel filled by TEUs (between 0 and 100')
    slot_revenue= col32.number_input('Enter Slot Market Price')

    col1, col2 = st.columns(2)
    do_bunker_price = col1.number_input('Enter DO Bunker Price')
    fo_bunker_price = col2.number_input('Enter VLSFO Bunker Price')

    configuration = cfg.Config(capacity=capacity, forty_feet_percentage=forty_feet_container_percent,
                               frequency=frequency, eca_distance=eca_distance, teu_percent=teu_capacity, slot_revenue=slot_revenue)
    do = cfg.DO(bunker_price=do_bunker_price)
    fo = cfg.FO(bunker_price=fo_bunker_price)
    costs = cfg.Costs()

    st.markdown('**Enter Vessel Path**')
    port_codes = port_information_df['Port Code'].unique()
    render_recursive_dropdowns(port_codes)

    if st.session_state['done_clicked']:
        port_distances_df = calculate.get_port_distance(st.session_state['selected_paths'], port_locations_df)

        distance_and_time_summary_table = calculate.collate_dataframe(port_information_df, port_distances_df, configuration)
        st.markdown(":blue[Port Information]")
        st.table(distance_and_time_summary_table)

        summations = calculate.calculate_totals(distance_and_time_summary_table, fuel_consumption_df, configuration)
        summations = calculate.fuel_consumption_on_sea(fuel_consumption_df, summations, configuration, do)
        summations = calculate.voyage_consumption(summations, do, fo)
        summations = calculate.bunker_consumption(summations, do, fo)
        total_costs_df = calculate.total_costs(summations, costs, configuration)
        total_costs_df = calculate.summary_table(total_costs_df, configuration)
        st.markdown(":blue[Summary]")
        st.markdown("**Distances (in Miles) and Times (in Days) for Varying Speeds**")
        st.table(summations)
        st.table(total_costs_df)


        trace_map.generate_map(port_distances_df)
