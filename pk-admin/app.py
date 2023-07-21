import hashlib
import streamlit as st
import sqlite3
import pandas as pd
import time
import subprocess
import matplotlib.pyplot as plt
import json
import numpy as np

correct_username = "admin"
correct_password = "admin"


DB='../database/accounts.db'

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Retrieve data from the database
cursor.execute("SELECT * FROM accounts")
results = cursor.fetchall()


df = pd.DataFrame(results, columns=[column[0] for column in cursor.description])




placeholder = st.empty()

# Login Page
def login_page():
    st.title("Login Page")
    if "session_token" not in st.session_state:
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == correct_username and password == correct_password:
                # Generate a session token using the hashed password
                session_token = hashlib.sha256(password.encode()).hexdigest()

                # Set the session token in the Streamlit session state
                st.session_state["session_token"] = session_token
                st.empty()
                st.success("login successful.")
                st.write("Logout before logging out.")
                logout()    
                    
            else:
                st.write("Invalid username or password")
    else:
        st.success("login successful.")
        st.write("Logout before logging out.")
        logout()
        
def logout():
    if st.button("logout"):
            conn.close()
            st.session_state.clear()
            st.write("Logged out successfully.")
            



# User Page
def user_page():
    st.title("User Page")
    st.write("Welcome to the User Page!")
    st.table(df)
    
# Display the DataFrame as a pie chart
    st.subheader("Data Visualization - Pie Chart")
    fig, ax = plt.subplots()
    ax.pie(df['vtype'].value_counts(), labels=df['vtype'].unique(), autopct='%1.1f%%')
    ax.set_aspect('equal')
    st.pyplot(fig)
    
# Delete and Insert datas

    st.subheader("Add Details")
    uname=st.text_input("Enter username")
    pswd=st.text_input("Enter password")
    email=st.text_input("Enter email")
    vtype=st.selectbox("Select your vehicle type:",("two_wheel","four_wheel"))
    if st.button("Add"):
        add_details(uname,pswd,email,vtype)
        
    st.subheader("Delete Users")
    row_index = st.number_input("Enter row index to delete", min_value=0, max_value=len(df)-1, step=1)       
    if st.button("Delete"):
        delete_row(row_index)

def add_details(uname,pswd,email,vtype):
    cursor = conn.cursor()
    cursor.execute("insert into accounts (username, password,email,vtype) values(?,?,?,?)",(uname, pswd, email, vtype))
    conn.commit()
    with st.spinner(text='In progress'):
        time.sleep(5)
        st.write("Details added to the 'accounts' table")
        st.experimental_rerun()

    
        
# Delete operation
def delete_row(row_index):
    # Perform the delete operation here
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts")
    results = cursor.fetchall()
    row_to_delete = results[row_index]

    cursor.execute("DELETE FROM accounts WHERE username=?", (row_to_delete[0],))
    conn.commit()
    st.write(f"Deleted row with username: {row_to_delete[0]}")
    
    with st.spinner(text='In progress'):
        time.sleep(5)
        st.experimental_rerun()


# Parking Management Page
def parking_management_page():
    st.title("Parking Management Page")
    st.write("Welcome to the Parking Management Page!")
    st.write("Here is the data from the 'manager' table:")

    # Fetch data from the 'manager' table
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM managers")
    results = cursor.fetchall()

    # Convert the results to a Pandas DataFrame
    df = pd.DataFrame(results, columns=[column[0] for column in cursor.description])

    # Display the DataFrame as a table using Streamlit
    st.table(df)
    show_managers_table()
    
def show_managers_table():
    st.title("Managers Table")

    # Fetch data for approval = 1
    cursor = conn.cursor()
    cursor.execute("SELECT mid, mname, memail, approval FROM managers WHERE approval = 1")
    results_1 = cursor.fetchall()
    print (results_1)
    df_1 = pd.DataFrame(results_1, columns=['mid', 'mname', 'memail', 'approval'])
    df_1['approval'] = df_1['approval'].map({1: 'Verified'})

    # Fetch data for approval = 0
    cursor.execute("SELECT mid, mname, memail, approval FROM managers WHERE approval = 0")
    results_2 = cursor.fetchall()
    df_2 = pd.DataFrame(results_2, columns=['mid', 'mname', 'memail', 'approval'])
    df_2['approval'] = df_2['approval'].map({0: 'Unverified'})

    # Display the tables
    st.subheader("Authenticated Managers Accounts")
    st.table(df_1)

    st.subheader("Unauthenticated Managers Accounts")
    for index, row in df_2.iterrows():
        st.write(f"Manager ID: {row['mid']}, Name: {row['mname']}, Email: {row['memail']}")
        verify_button = st.button(f"Verify Manager {row['mid']}")
        if verify_button:
            verify_manager(row['mid'])
    
    cursor.execute("SELECT mname,slot1,slot2 FROM managers WHERE approval = 1")
    result_bar = cursor.fetchall()
    print(result_bar)
    bar_data = []
    for result in result_bar:
        jslot1 = json.loads(result[1])
        jslot2 = json.loads(result[2])
        bar_data.append((result[0],jslot1.get('t1')+jslot2.get('t1'), jslot1.get('motorcycle')+jslot2.get('motorcycle')+jslot1.get('car')+jslot2.get('car')+jslot1.get('truck')+jslot2.get('truck')))
           
    print("bar data: ",bar_data)
    df_bar = pd.DataFrame(bar_data, columns=['manager name', 'total capacity', 'occupancy'])
    print(df_bar)
    
    st.subheader("Bar Chart Data")
    st.dataframe(df_bar)
    
    manager_names = [item[0] for item in bar_data]
    total_values = [item[1] for item in bar_data]
    occupancy_values = [item[2] for item in bar_data]

    x = np.arange(len(manager_names))
    bar_width = 0.35

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - bar_width/2, total_values, bar_width, label='Total')
    rects2 = ax.bar(x + bar_width/2, occupancy_values, bar_width, label='Occupancy')

    ax.set_xlabel('Manager Names')
    ax.set_ylabel('Count')
    ax.set_title('Manager Count: Total vs Occupancy')
    ax.set_xticks(x)
    ax.set_xticklabels(manager_names)
    ax.legend()

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    st.pyplot(fig)
    
    
def verify_manager(manager_id):
    # Perform the verification operation here
    cursor = conn.cursor()
    cursor.execute("UPDATE managers SET approval = 1 WHERE mid = ?", (manager_id,))
    conn.commit()
    st.write(f"Manager {manager_id} has been verified.")


# Main Application
def main():
    st.sidebar.title("Navigation")
    page_options = ["Login", "User Page", "Parking Management"]
    selection = st.sidebar.radio("Go to", page_options)

    if selection == "Login":
        login_page()
    elif selection == "User Page":
        if "session_token" not in st.session_state:
            st.title("User Details")
            st.write("Please Login!!")
        else:
            user_page()
            
    elif selection == "Parking Management":
        if "session_token" not in st.session_state:
            st.title("User Details")
            st.write("Please Login!!")
        else:
            parking_management_page()


if __name__ == "__main__":
    main()
