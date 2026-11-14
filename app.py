import streamlit as st
import pandas as pd
import sqlite3

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Setup
DB_FILE = 'stats_hub.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, question TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, reply TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# 3. Admin Login Setup (In Sidebar)
st.sidebar.title("Navigation")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    with st.sidebar.expander("🔐 Admin Login"):
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == st.secrets.get("ADMIN_PASSWORD", "JamesAdmin2024"):
                st.session_state.is_admin = True
                st.success("Logged in as Admin!")
                st.rerun()
            else:
                st.error("Incorrect password")
else:
    st.sidebar.success("👑 Logged in as Admin")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()

page = st.sidebar.radio("Go to", ["Home", "Timetable", "Notice Board", "Resource Vault", "Class Forum", "Live Chat"])

is_admin = st.session_state.is_admin 

# --- HOME PAGE ---
if page == "Home":
    st.title("Welcome to the Kirinyaga Stats Hub! 📊")
    st.write("This is a central platform for all BSc Statistics students at Kirinyaga University.")
    st.write("Use the sidebar to check your timetable, read notices, access past papers, and stay updated.")
    st.info("Built by James Kiruma using Python and Streamlit.")

# --- TIMETABLE PAGE (FULLY CORRECTED) ---
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    st.write("**Bachelor of Science in Statistics | Stage: Y2.S1 (August - December 2026/2027)**")
    
    # The exact data from your notebook
    timetable_data = {
        "Day": ["Monday", "Tuesday", "Tuesday", "Wednesday", "Wednesday", "Wednesday", "Thursday", "Friday"],
        "Time": ["NO LECTURES", "7:00am - 10:00am", "10:00am - 1:00pm", "10:00am - 1:00pm", "1:00pm - 4:00pm", "4:00pm - 7:00pm", "NO LECTURES", "10:00am - 1:00pm"],
        "Unit Code": ["-", "STA 2243", "SPM 2302", "SPM 2321", "STA 2344", "STA 2342", "-", "STA 2240"],
        "Unit Name": ["-", "FUNDAMENTALS OF COMPUTER INTERACTIVE STATISTICS", "NUMERICAL ANALYSIS I", "INTRODUCTION TO EPIDEMIOLOGICAL METHODS", "CALCULUS FOR STATISTICS III", "-", "-", "PROBABILITY AND STATISTICS II"],
        "Venue": ["-", "LAB 1", "JSM 105", "JSM 001", "LAB", "-", "-", "JSM 101"],
        "Lecturer": ["-", "Dr. Mutua", "Dr. Kayiita", "Mr. Muchondou", "Carol", "Dr. Moffat C.N.", "-", "Lucas"]
    }
    
    df = pd.DataFrame(timetable_data)
    
    # Display as a clean table
    st.dataframe(df, width="stretch", hide_index=True)
