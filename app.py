import streamlit as st
import pandas as pd
import sqlite3
import os

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Setup
DB_FILE = 'stats_hub.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT)''')
    conn.commit()
    conn.close()

# Run this once when the app starts
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Timetable", "Notice Board", "Resource Vault"])

# --- HOME PAGE ---
if page == "Home":
    st.title("Welcome to the Kirinyaga Stats Hub! 📊")
    st.write("This is a central platform for all BSc Statistics students at Kirinyaga University.")
    st.write("Use the sidebar to check your timetable, read notices, access past papers, and stay updated.")
    st.info("Built by James Kiruma using Python and Streamlit.")

# --- TIMETABLE PAGE ---
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    st.write("Here is the schedule for this semester.")

    timetable_data = {
        "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "8:00 AM - 10:00 AM": ["Calculus III", "Probability II", "Epidemiology", "Linear Algebra II", "Calculus III"],
        "10:00 AM - 12:00 PM": ["Linear Algebra II", "Calculus III", "Probability II", "Epidemiology", "Stats Computing"],
        "2:00 PM - 4:00 PM": ["Epidemiology", "Stats Computing", "Calculus III", "Probability II", "Linear Algebra II"]
    }
    
    df = pd.DataFrame(timetable_data)
    st.dataframe(df, use_container_width=True)

# --- NOTICE BOARD PAGE ---
elif page == "Notice Board":
    st.title("📌 Notice Board")
    
    # Form to add a notice
    with st.form("notice_form", clear_on_submit=True):
        new_notice = st.text_area("Type a new notice for the class:")
        submitted = st.form_submit_button("Post Notice")
        
        if submitted and new_notice:
            conn = get_db_connection()
            conn.execute('INSERT INTO notices (message) VALUES (?)', (new_notice,))
            conn.commit()
            conn.close()
            st.success("Notice posted successfully!")
            st.rerun()

    st.divider()
    st.subheader("Latest Updates")
    
    # Fetch and display notices from database
    conn = get_db_connection()
    notices = conn.execute('SELECT message FROM notices ORDER BY id DESC').fetchall()
    conn.close()
    
    if len(notices) == 0:
        st.info("No notices posted yet. Be the first!")
    else:
        for notice in notices:
            st.success(notice['message'])

# --- RESOURCE VAULT PAGE ---
elif page == "Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Add past papers or notes to the database.")
    
    with st.form("upload_form", clear_on_submit=True):
        unit_code = st.text_input("Unit Code (e.g., STA 2101)")
        title = st.text_input("Resource Title (e.g., CAT 1 Past Paper)")
        uploaded_file = st.file_uploader("Upload file (PDF, DOCX)", type=["pdf", "docx"])
        
        submit_resource = st.form_submit_button("Save to Vault")
        
        if submit_resource and unit_code and title and uploaded_file:
            conn = get_db_connection()
            # Save just the file name to the database for now
            conn.execute('INSERT INTO resources (unit_code, title, file_name) VALUES (?, ?, ?)', 
                         (unit_code, title, uploaded_file.name))
            conn.commit()
            conn.close()
            st.success(f"Saved {title} to database!")
            st.rerun()
    
    st.divider()
    st.subheader("Available Resources")
    
    conn = get_db_connection()
    resources = conn.execute('SELECT unit_code, title, file_name FROM resources ORDER BY id DESC').fetchall()
    conn.close()
    
    if len(resources) == 0:
        st.info("No resources added yet.")
    else:
        # Convert to list of dicts for pandas
        df_resources = pd.DataFrame([dict(r) for r in resources])
        st.dataframe(df_resources, use_container_width=True)
