import streamlit as st
import pandas as pd
import sqlite3

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Connection Function
def get_db_connection():
    conn = sqlite3.connect('stats_hub.db')
    conn.row_factory = sqlite3.Row # This lets us access columns by name
    return conn

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
# Added "Resource Vault" to the options!
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
    st.write("Latest updates for the class.")
    
    # Keep your static notices
    st.success("✅ Update (Nov 14): CAT results for Linear Algebra II are expected next week.")
    st.warning("⚠️ Reminder: Submit your Stats Computing assignment by Friday.")

    st.divider()
    
    # NEW: Let students add dynamic notices
    st.subheader("Add a new notice")
    with st.form("notice_form"):
        new_notice = st.text_area("Type your notice here:")
        submitted = st.form_submit_button("Post Notice")
        
        if submitted and new_notice:
            # Here is where we would normally save to the database. 
            # For now, we will just show it worked!
            st.write(f"*(Pending Database Save)*: {new_notice}")

# --- RESOURCE VAULT PAGE ---
elif page == "Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Upload and download past papers, notes, and R/Python scripts.")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload a past paper or notes (PDF, DOCX)", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        st.success(f"File '{uploaded_file.name}' selected! (Database integration coming next).")
    
    st.divider()
    
    # Display existing resources
    st.subheader("Available Resources")
    # Hardcoded for now, later we pull this from the SQLite database
    resources = pd.DataFrame({
        "Unit Code": ["STA 2101", "STA 2102", "STA 2103"],
        "Title": ["Calculus III CAT 1", "Linear Algebra II Notes", "Probability II Past Paper"],
        "Uploaded By": ["James K.", "Admin", "Class Rep"]
    })
    st.table(resources)
