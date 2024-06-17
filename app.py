import streamlit as st
import pandas as pd
import pickle
import os
from database import create_connection, initialize_database, insert_data, fetch_data

# Database setup
conn = create_connection('example.db')
initialize_database(conn)

# Load the trained models
current_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(current_dir, 'best_model.pkl'), 'rb') as model_file:
    input_weight_model = pickle.load(model_file)
with open(os.path.join(current_dir, 'machining_model.pkl'), 'rb') as model_file:
    machining_model = pickle.load(model_file)
with open(os.path.join(current_dir, 'inspection_model.pkl'), 'rb') as model_file:
    inspection_model = pickle.load(model_file)

# Final landed cost based on grade type
final_landed_cost = {
    '1  MT  XX (25-95 dia)': 103,
    '1  MT  XX (100-210 dia)': 113,
    '1  MT YY (25-95 dia)': 160,
    '1  MT  YY (100-125 dia)': 173,
    '1  MT  XY (25-95 dia))': 106,
    '1  MT  8319 (100-210 dia)':116,
    '1  MT  8319':104
}

# Function to calculate raw material cost
def calculate_raw_material_cost(process_type, input_weight, grade_type):
    if process_type == 0:  # 0 represents casting
        return 0
    elif process_type == 1:  # 1 represents forging
        return input_weight * final_landed_cost[grade_type]

# Function to calculate process cost
def calculate_process_cost(process_type, input_weight):
    if process_type == 0:  # 0 represents casting
        return (input_weight * (120.57788 / 1000) * 1000)
    elif process_type == 1:  # 1 represents forging
        return input_weight * 30

# Streamlit interface
st.title("EX-Works Calculator")

# Page navigation
pages = ["Home", "Vendor Data", "Material Data", "RM Cost Data", "Supplier Data"]
page = st.sidebar.selectbox("Select Page", pages)

if page == "Home":
    st.write("Welcome to the EX-Works Calculator application.")

elif page == "Vendor Data":
    st.header("Vendor Data")
    vendor_name = st.text_input("Vendor Name")
    vendor_type = st.text_input("Vendor Type")
    gst_no =st.number_input("GST NO")
    contact_person_name=st.text_input("CONTACT PERSON/NAME")
    address=st.text_input("ADDRESS")
    city=st.text_input("CITY")
    panno=st.text_input("PAN NO")
    
    if st.button("Add Vendor"):
        vendor_data = pd.DataFrame({'vendor_name': [vendor_name], 'vendor_type': [vendor_type], 'GST_NO': [gst_no], 'Contact_person_name': [contact_person_name], 'address': [address], 'city': [city], 'pan_no':[panno]})
        insert_data(conn, 'vendor_data', vendor_data)
        st.success("Vendor data added successfully")

elif page == "Material Data":
    st.header("Material Data")
    material_type = st.text_input("Material Type")
    material_info = st.text_input("Material Info")
    
    if st.button("Add Material"):
        material_data = pd.DataFrame({'material_type': [material_type], 'material_info': [material_info]})
        insert_data(conn, 'material_data', material_data)
        st.success("Material data added successfully")

elif page == "RM Cost Data":
    st.header("RM Cost Data")
    rm_type = st.text_input("RM Type")
    rm_cost = st.number_input("RM Cost", min_value=0.0, step=0.01)
    vendor_id = st.number_input("Vendor ID", min_value=1, step=1)
    
    if st.button("Add RM Cost Data"):
        rm_cost_data = pd.DataFrame({'rm_type': [rm_type], 'rm_cost': [rm_cost], 'vendor_id': [vendor_id]})
        insert_data(conn, 'rm_cost_data', rm_cost_data)
        st.success("RM cost data added successfully")

elif page == "Supplier Data":
    st.header("Supplier Data")
    part_no = st.number_input("Part No", min_value=1, step=1)
    process_type = st.selectbox("Process Type", options=[0, 1])
    part_od = st.number_input("Part OD", min_value=0.0, step=0.1)
    part_id = st.number_input("Part ID", min_value=0.0, step=0.1)
    part_width = st.number_input("Part Width", min_value=0, step=1)
    finish_wt = st.number_input("Finish Wt", min_value=0.0, step=0.1)
    grade_type = st.selectbox("Grade Type", options=list(final_landed_cost.keys()))
    material_id = st.number_input("Material ID", min_value=1, step=1)
    
    if st.button("Calculate and Add Supplier Data"):
        # Prepare the input data for prediction
        input_data = pd.DataFrame({
            'Process type': [process_type],
            'Part Od': [part_od],
            'Part ID': [part_id],
            'Part Width': [part_width],
            'Finish Wt': [finish_wt]
        })

        # Predict the input weight
        predicted_input_weight = input_weight_model.predict(input_data)[0]

        # Calculate raw material cost
        raw_material_cost = calculate_raw_material_cost(process_type, predicted_input_weight, grade_type)
        
        # Calculate process cost
        process_cost = calculate_process_cost(process_type, predicted_input_weight)
        
        # Prepare the data for machining time prediction
        machining_data = pd.DataFrame({
            'Process type': [process_type],
            'Part Od': [part_od],
            'Part ID': [part_id],
            'Part Width': [part_width],
            'Finish Wt': [finish_wt],
            'Input Weight': [predicted_input_weight],
            'Raw material cost': [raw_material_cost],
            'Process cost': [process_cost]
        })

        # Predict the machining time
        predicted_machining_time = machining_model.predict(machining_data)[0]

        # Calculate machining cost
        machining_cost = predicted_machining_time * 375.71
        
        # Calculate scrap recovery
        scrap_recovery = (predicted_input_weight - finish_wt) * 11.5
        
        # Prepare the data for inspection time prediction
        inspection_data = pd.DataFrame({
            'Process type': [process_type],
            'Part Od': [part_od],
            'Part ID': [part_id],
            'Part Width': [part_width],
            'Finish Wt': [finish_wt],
            'Input Weight': [predicted_input_weight],
            'Raw material cost': [raw_material_cost],
            'Process cost': [process_cost],
            'Machining Time': [predicted_machining_time],
            'Machining cost': [machining_cost],
            'Scrap recovery': [scrap_recovery]
        })

        # Predict the inspection time
        predicted_inspection_time = inspection_model.predict(inspection_data)[0]

        # Calculate inspection cost
        inspection_cost = predicted_inspection_time * 375.71
        
        # Calculate total mg cost
        total_mg_cost = raw_material_cost + process_cost + machining_cost + scrap_recovery + inspection
