import streamlit as st
import pandas as pd
import sqlite3

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Setup
DB_FILE = 'stats_hub_v2.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT, file_data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, question TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, reply_name TEXT, reply TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# 3. Admin Login
st.sidebar.title("Navigation")
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    with st.sidebar.expander("🔐 Admin Login"):
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if password == st.secrets.get("ADMIN_PASSWORD", "JamesAdmin2024"):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Incorrect")
else:
    st.sidebar.success("👑 Admin")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()

# LIVE CHAT IS BACK IN THE MENU
page = st.sidebar.radio("Go to", ["Home", "Timetable", "Notice Board", "Resource Vault", "Class Forum", "Live Chat"])
is_admin = st.session_state.is_admin 

# --- HOME PAGE ---
if page == "Home":
    st.title("Welcome to the Kirinyaga Stats Hub! 📊")
    st.info("Built by James Kiruma using Python and Streamlit.")

# --- TIMETABLE PAGE ---
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    timetable_data = {
        "Day": ["Monday", "Tuesday", "Tuesday", "Wednesday", "Wednesday", "Wednesday", "Thursday", "Friday"],
        "Time": ["NO LECTURES", "7:00am - 10:00am", "10:00am - 1:00pm", "10:00am - 1:00pm", "1:00pm - 4:00pm", "4:00pm - 7:00pm", "NO LECTURES", "10:00am - 1:00pm"],
        "Unit Code": ["-", "STA 2243", "SPM 2302", "SPM 2321", "STA 2344", "STA 2342", "-", "STA 2240"],
        "Unit Name": ["-", "Fundamentals of Computer Interactive Stats", "Linear Algebra II", "Numerical Analysis I", "Intro to Epidemiological Methods", "Calculus for Statistics III", "-", "Probability and Statistics II"],
        "Venue": ["-", "LAB 1", "JSM 105", "JSM 001", "LH 19", "-", "-", "JSM 101"]
    }
    st.dataframe(pd.DataFrame(timetable_data), width="stretch", hide_index=True)

# --- NOTICE BOARD PAGE ---
elif page == "Notice Board":
    st.title("📌 Notice Board")
    
    new_notice = st.text_area("Type a new notice for the class:", key="notice_input")
    if st.button("Post Notice", key="btn_notice"):
        if new_notice:
            conn = get_db_connection()
            conn.execute('INSERT INTO notices (message) VALUES (?)', (new_notice,))
            conn.commit()
            conn.close()
            st.rerun()

    st.divider()
    conn = get_db_connection()
    notices = conn.execute('SELECT id, message FROM notices ORDER BY id DESC').fetchall()
    for notice in notices:
        if is_admin:
            col1, col2 = st.columns([5, 1])
            with col1: st.success(notice['message'])
            with col2:
                if st.button("🗑️", key=f"del_notice_{notice['id']}"):
                    conn.execute('DELETE FROM notices WHERE id = ?', (notice['id'],))
                    conn.commit()
                    st.rerun()
        else:
            st.success(notice['message'])
    conn.close()

# --- RESOURCE VAULT PAGE ---
elif page == "Resource Vault":
    st.title("📚 Resource Vault")
    
    unit_code = st.text_input("Unit Code:", key="res_code")
    title = st.text_input("Resource Title:", key="res_title")
    uploaded_file = st.file_uploader("Upload file", type=["pdf", "docx"], key="res_file")
    
    if st.button("Save to Vault", key="btn_save_res"):
        if unit_code and title and uploaded_file:
            file_bytes = uploaded_file.read()
            conn = get_db_connection()
            conn.execute('INSERT INTO resources (unit_code, title, file_name, file_data) VALUES (?, ?, ?, ?)', 
                         (unit_code, title, uploaded_file.name, file_bytes))
            conn.commit()
            conn.close()
            st.success("Saved!")
            st.rerun()
        else:
            st.error("Fill all fields.")

    st.divider()
    conn = get_db_connection()
    resources = conn.execute('SELECT id, unit_code, title, file_name, file_data FROM resources ORDER BY id DESC').fetchall()
    for r in resources:
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1: st.write(f"**{r['unit_code']}**")
        with col2: st.write(r['title'])
        with col3:
            if r['file_data']:
                st.download_button("⬇️ Download", data=r['file_data'], file_name=r['file_name'], mime="application/pdf", key=f"dl_{r['id']}")
        with col4:
            if is_admin:
                if st.button("🗑️", key=f"del_res_{r['id']}"):
                    conn.execute('DELETE FROM resources WHERE id = ?', (r['id'],))
                    conn.commit()
                    st.rerun()
    conn.close()

# --- CLASS FORUM PAGE ---
elif page == "Class Forum":
    st.title("💬 Class Q&A Forum")
    
    if is_admin:
        if st.button("🗑️ Clear All Questions", key="btn_clear_all"):
            conn = get_db_connection()
            conn.execute('DELETE FROM questions')
            conn.execute('DELETE FROM replies')
            conn.commit()
            conn.close()
            st.rerun()

    st.divider()

    # Ask Question
    q_name = st.text_input("Your Name:", key="q_name")
    q_text = st.text_area("Your Question:", key="q_text")
    if st.button("Post Question", key="btn_post_q"):
        if q_name and q_text:
            conn = get_db_connection()
            conn.execute('INSERT INTO questions (name, question) VALUES (?, ?)', (q_name, q_text))
            conn.commit()
            conn.close()
            st.rerun()
        else:
            st.warning("Please enter both name and question.")

    st.divider()
    
    # Display Questions & Replies
    conn = get_db_connection()
    questions = conn.execute('SELECT id, name, question FROM questions ORDER BY id DESC').fetchall()
    
    for q in questions:
        st.markdown(f"**{q['name']}** asked: *{q['question']}*")
        
        replies = conn.execute('SELECT reply_name, reply FROM replies WHERE question_id = ?', (q['id'],)).fetchall()
        for r in replies:
            st.markdown(f"↳ 💬 **{r['reply_name']}** replied: {r['reply']}")
            
        col1, col2 = st.columns([1, 3])
        with col1: r_name = st.text_input("Name", key=f"r_name_{q['id']}", label_visibility="collapsed", placeholder="Your Name")
        with col2: r_text = st.text_input("Reply", key=f"r_text_{q['id']}", label_visibility="collapsed", placeholder="Reply here...")
        
        if st.button("Reply", key=f"btn_reply_{q['id']}"):
            if r_name and r_text:
                conn.execute('INSERT INTO replies (question_id, reply_name, reply) VALUES (?, ?, ?)', (q['id'], r_name, r_text))
                conn.commit()
                st.rerun()
            else:
                st.warning("Fill both fields to reply.")
                
        if is_admin:
            if st.button("🗑️ Delete Question", key=f"del_q_{q['id']}"):
                conn.execute('DELETE FROM replies WHERE question_id = ?', (q['id'],))
                conn.execute('DELETE FROM questions WHERE id = ?', (q['id'],))
                conn.commit()
                st.rerun()
                
        st.divider()
    conn.close()

# --- LIVE CHAT PAGE (RESTORED) ---
elif page == "Live Chat":
    st.title("⚡ Live Chat Room")
    st.write("Chat with classmates in real-time.")
    
    if is_admin:
        if st.button("🗑️ Clear Chat History", type="primary"):
            st.session_state.messages = []
            st.rerun()
        
    st.divider()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        response = f"Echo: {prompt}"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
