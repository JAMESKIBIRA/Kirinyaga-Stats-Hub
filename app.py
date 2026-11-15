import streamlit as st
import pandas as pd
import sqlite3

# 1. Page Configuration (Customizing the vibe)
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# 2. Custom CSS for that modern, sleek Gen Z look
st.markdown("""
<style>
    /* Main background and font */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Style standard buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid #e0e0e0;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Custom Card Style for Forum */
    .forum-card {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #4A90E2;
    }
    
    /* Custom text styling */
    .big-font {
        font-size: 24px;
        font-weight: 800;
        color: #1E1E1E;
    }
    .reply-text {
        background-color: #f1f3f5;
        padding: 10px 15px;
        border-radius: 10px;
        margin-top: 10px;
        font-size: 14px;
    }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. Database Setup
DB_FILE = 'stats_hub_v3.db'

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

# 4. Sidebar Navigation & Admin
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>✨ Stats Hub ✨</h1>", unsafe_allow_html=True)
    
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if not st.session_state.is_admin:
        with st.expander("🔐 Admin Login"):
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if password == st.secrets.get("ADMIN_PASSWORD", "JamesAdmin2024"):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Incorrect")
    else:
        st.success("👑 Admin Mode")
        if st.button("Logout"):
            st.session_state.is_admin = False
            st.rerun()
            
    st.divider()
    page = st.radio("Go to", ["🏠 Home", "📅 Timetable", "📌 Notice Board", "📚 Resource Vault", "💬 Class Forum", "⚡ Live Chat"])
    is_admin = st.session_state.is_admin 


# --- HOME PAGE ---
if page == "🏠 Home":
    st.markdown("<h1 style='text-align: center;'>Welcome to the Kirinyaga Stats Hub! 📊</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>The ultimate centralized platform for all BSc Statistics students at Kirinyaga University. No more scrolling through endless WhatsApp messages! 💅✨</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📅 **Timetable**\nCheck your classes.")
    with col2:
        st.info("📚 **Vault**\nDownload past papers.")
    with col3:
        st.info("💬 **Forum**\nAsk & answer questions.")

# --- TIMETABLE PAGE ---
elif page == "📅 Timetable":
    st.title("📅 Class Timetable")
    st.write("**Stage: Y2.S1 (August - December 2026/2027)**")
    
    timetable_data = {
        "Day": ["Monday", "Tuesday", "Tuesday", "Wednesday", "Wednesday", "Wednesday", "Thursday", "Friday"],
        "Time": ["NO LECTURES 😴", "7:00am - 10:00am", "10:00am - 1:00pm", "10:00am - 1:00pm", "1:00pm - 4:00pm", "4:00pm - 7:00pm", "NO LECTURES 😴", "10:00am - 1:00pm"],
        "Unit Code": ["-", "STA 2243", "SPM 2302", "SPM 2321", "STA 2344", "STA 2342", "-", "STA 2240"],
        "Unit Name": ["-", "Fundamentals of Computer Interactive Stats", "Linear Algebra II", "Numerical Analysis I", "Intro to Epidemiological Methods", "Calculus for Statistics III", "-", "Probability and Statistics II"],
        "Venue": ["-", "LAB 1", "JSM 105", "JSM 001", "LH 19", "-", "-", "JSM 101"]
    }
    st.dataframe(pd.DataFrame(timetable_data), width="stretch", hide_index=True)

# --- NOTICE BOARD PAGE ---
elif page == "📌 Notice Board":
    st.title("📌 Notice Board")
    
    new_notice = st.text_area("Drop a new notice here 📢:", key="notice_input")
    if st.button("Post Notice 🚀", key="btn_notice"):
        if new_notice:
            conn = get_db_connection()
            conn.execute('INSERT INTO notices (message) VALUES (?)', (new_notice,))
            conn.commit()
            conn.close()
            st.rerun()

    st.divider()
    conn = get_db_connection()
    notices = conn.execute('SELECT id, message FROM notices ORDER BY id DESC').fetchall()
    
    if not notices:
        st.write("No notices yet. Be the first! ✨")
        
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
elif page == "📚 Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Securing the bag with past papers and notes. 💸")
    
    with st.expander("➕ Upload a new resource"):
        unit_code = st.text_input("Unit Code (e.g., STA 2101):", key="res_code")
        title = st.text_input("Resource Title (e.g., CAT 1):", key="res_title")
        uploaded_file = st.file_uploader("Upload file", type=["pdf", "docx"], key="res_file")
        
        if st.button("Save to Vault 💾", key="btn_save_res"):
            if unit_code and title and uploaded_file:
                file_bytes = uploaded_file.read()
                conn = get_db_connection()
                conn.execute('INSERT INTO resources (unit_code, title, file_name, file_data) VALUES (?, ?, ?, ?)', 
                             (unit_code, title, uploaded_file.name, file_bytes))
                conn.commit()
                conn.close()
                st.success("Saved successfully! 🎉")
                st.rerun()
            else:
                st.error("Fill all fields.")

    st.divider()
    conn = get_db_connection()
    resources = conn.execute('SELECT id, unit_code, title, file_name, file_data FROM resources ORDER BY id DESC').fetchall()
    
    if not resources:
        st.write("Vault is empty. Upload something! 📂")
        
    for r in resources:
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1: st.markdown(f"**{r['unit_code']}**")
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

# --- CLASS FORUM PAGE (Modernized with Cards) ---
elif page == "💬 Class Forum":
    st.title("💬 Class Q&A Forum")
    st.write("Ask questions, share answers, and help the squad out. 🤝")
    
    if is_admin:
        if st.button("🗑️ Clear All Questions", key="btn_clear_all"):
            conn = get_db_connection()
            conn.execute('DELETE FROM questions')
            conn.execute('DELETE FROM replies')
            conn.commit()
            conn.close()
            st.rerun()

    st.divider()

    # Ask Question Form
    with st.container():
        q_name = st.text_input("Your Name:", key="q_name", placeholder="e.g., James K.")
        q_text = st.text_area("What's your question?", key="q_text", placeholder="Type here...")
        if st.button("Post Question 🚀", key="btn_post_q"):
            if q_name and q_text:
                conn = get_db_connection()
                conn.execute('INSERT INTO questions (name, question) VALUES (?, ?)', (q_name, q_text))
                conn.commit()
                conn.close()
                st.rerun()
            else:
                st.warning("Fill in both fields!")

    st.divider()
    
    # Display Questions as Cards
    conn = get_db_connection()
    questions = conn.execute('SELECT id, name, question FROM questions ORDER BY id DESC').fetchall()
    
    if not questions:
        st.info("No questions yet. Ask the first one! 👀")
        
    for q in questions:
        # HTML Card styling for the question
        st.markdown(f"""
        <div class="forum-card">
            <span style='font-size: 20px;'>🗣️</span> <b style='font-size: 16px;'>{q['name']}</b> asked:<br>
            <span style='font-size: 16px;'>{q['question']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show replies
        replies = conn.execute('SELECT reply_name, reply FROM replies WHERE question_id = ?', (q['id'],)).fetchall()
        for r in replies:
            st.markdown(f"<div class='reply-text'>↳ 💬 <b>{r['reply_name']}</b>: {r['reply']}</div>", unsafe_allow_html=True)
            
        st.write("") # Spacing
        
        # Reply inputs
        with st.expander("Reply to this 👇"):
            col1, col2 = st.columns([1, 2])
            with col1: r_name = st.text_input("Name", key=f"r_name_{q['id']}", placeholder="Your Name")
            with col2: r_text = st.text_input("Reply", key=f"r_text_{q['id']}", placeholder="Type your reply...")
            
            if st.button("Reply 💬", key=f"btn_reply_{q['id']}"):
                if r_name and r_text:
                    conn.execute('INSERT INTO replies (question_id, reply_name, reply) VALUES (?, ?, ?)', (q['id'], r_name, r_text))
                    conn.commit()
                    st.rerun()
                else:
                    st.warning("Enter name and reply.")
                    
            if is_admin:
                if st.button("🗑️ Delete Question", key=f"del_q_{q['id']}"):
                    conn.execute('DELETE FROM replies WHERE question_id = ?', (q['id'],))
                    conn.execute('DELETE FROM questions WHERE id = ?', (q['id'],))
                    conn.commit()
                    st.rerun()
                    
        st.divider()
    conn.close()

# --- LIVE CHAT PAGE ---
elif page == "⚡ Live Chat":
    st.title("⚡ Live Chat Room")
    st.write("Real-time vibes. Chat with the class. 🗣️")
    
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
        
        # Simple bot response just for UI feel
        response = f"Received: {prompt}"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
