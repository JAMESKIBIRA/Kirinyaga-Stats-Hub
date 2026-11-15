import streamlit as st
import pandas as pd
import sqlite3
import base64

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Setup
DB_FILE = 'stats_hub.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)''')
    # Notice we added a 'file_data' BLOB column to store the actual PDF!
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT, file_data BLOB)''')
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
    st.info("Built by James Kiruma using Python and Streamlit.")

# --- TIMETABLE PAGE ---
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    timetable_data = {
        "Day": ["Monday", "Tuesday", "Tuesday", "Wednesday", "Wednesday", "Wednesday", "Thursday", "Friday"],
        "Time": ["NO LECTURES", "7:00am - 10:00am", "10:00am - 1:00pm", "10:00am - 1:00pm", "1:00pm - 4:00pm", "4:00pm - 7:00pm", "NO LECTURES", "10:00am - 1:00pm"],
        "Unit Code": ["-", "STA 2243", "SPM 2302", "SPM 2321", "STA 2344", "STA 2342", "-", "STA 2240"],
        "Unit Name": ["-", "Fundamentals of Computer Interactive Statistics", "Linear Algebra II", "Numerical Analysis I", "Introduction to Epidemiological Methods", "Calculus for Statistics III", "-", "Probability and Statistics II"],
        "Venue": ["-", "LAB 1", "JSM 105", "JSM 001", "LH 19", "-", "-", "JSM 101"],
        "Lecturer": ["-", "Dr. Mutua", "Dr. Kayiita", "Muthondu", "Carol", "Dr. Moffat C.N.", "-", "Lucas"]
    }
    df = pd.DataFrame(timetable_data)
    st.dataframe(df, width="stretch", hide_index=True)

# --- RESOURCE VAULT PAGE (UPDATED) ---
elif page == "Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Upload and download past papers or notes.")
    
    with st.form("upload_form", clear_on_submit=True):
        unit_code = st.text_input("Unit Code (e.g., STA 2101)")
        title = st.text_input("Resource Title (e.g., CAT 1 Past Paper)")
        uploaded_file = st.file_uploader("Upload file (PDF, DOCX)", type=["pdf", "docx"])
        submit_resource = st.form_submit_button("Save to Vault")
        
        if submit_resource and unit_code and title and uploaded_file:
            # Read the file as binary data
            file_bytes = uploaded_file.read()
            
            conn = get_db_connection()
            conn.execute('INSERT INTO resources (unit_code, title, file_name, file_data) VALUES (?, ?, ?, ?)', 
                         (unit_code, title, uploaded_file.name, file_bytes))
            conn.commit()
            conn.close()
            st.success(f"Saved {title} to database!")
            st.rerun()
    
    st.divider()
    
    if is_admin:
        if st.button("🗑️ Clear All Resources"):
            conn = get_db_connection()
            conn.execute('DELETE FROM resources')
            conn.commit()
            conn.close()
            st.success("All resources cleared!")
            st.rerun()

    st.subheader("Available Resources")
    conn = get_db_connection()
    resources = conn.execute('SELECT id, unit_code, title, file_name, file_data FROM resources ORDER BY id DESC').fetchall()
    
    if len(resources) == 0:
        st.info("No resources added yet.")
    else:
        for r in resources:
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            with col1:
                st.write(f"**{r['unit_code']}**")
            with col2:
                st.write(f"{r['title']}")
            with col3:
                # THIS IS THE MAGIC DOWNLOAD BUTTON
                if r['file_data'] is not None:
                    st.download_button(
                        label="⬇️ Download File",
                        data=r['file_data'],
                        file_name=r['file_name'],
                        mime="application/pdf",
                        key=f"download_{r['id']}"
                    )
                else:
                    st.write("*(File not saved, please re-upload)*")
            with col4:
                if is_admin:
                    if st.button("🗑️", key=f"del_res_{r['id']}"):
                        conn.execute('DELETE FROM resources WHERE id = ?', (r['id'],))
                        conn.commit()
                        st.rerun()
    conn.close()

# --- NOTICE BOARD PAGE (Shortened for brevity, it stays the same) ---
elif page == "Notice Board":
    st.title("📌 Notice Board")
    # ... (Keep your existing Notice Board code here) ...
    st.write("Notice board code goes here.")

# --- CLASS FORUM PAGE (Shortened) ---
elif page == "Class Forum":
    st.title("💬 Class Q&A Forum")
    # ... (Keep your existing Forum code here) ...
    st.write("Forum code goes here.")

# --- LIVE CHAT PAGE (Shortened) ---
elif page == "Live Chat":
    st.title("⚡ Live Chat Room")
    # ... (Keep your existing Live Chat code here) ...
    st.write("Live Chat code goes here.")
