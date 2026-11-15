import streamlit as st
import pandas as pd
import sqlite3
import os

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="📊", layout="wide")

# 2. Database Setup
DB_FILE = 'stats_hub.db'

def init_db():
    # Force delete the old database to fix the caching error
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT, file_data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, question TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, reply_name TEXT, reply TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Run this once when the app starts
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

# --- TIMETABLE PAGE ---
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    st.write("**Bachelor of Science in Statistics | Stage: Y2.S1 (August - December 2026/2027)**")
    
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

# --- NOTICE BOARD PAGE ---
elif page == "Notice Board":
    st.title("📌 Notice Board")
    
    new_notice = st.text_area("Type a new notice for the class:")
    if st.button("Post Notice"):
        if new_notice:
            conn = get_db_connection()
            conn.execute('INSERT INTO notices (message) VALUES (?)', (new_notice,))
            conn.commit()
            conn.close()
            st.success("Notice posted successfully!")
            st.rerun()
        else:
            st.error("Please type a notice before posting.")

    st.divider()
    
    if is_admin:
        if st.button("🗑️ Clear All Notices"):
            conn = get_db_connection()
            conn.execute('DELETE FROM notices')
            conn.commit()
            conn.close()
            st.success("All notices cleared!")
            st.rerun()

    st.subheader("Latest Updates")
    conn = get_db_connection()
    notices = conn.execute('SELECT id, message FROM notices ORDER BY id DESC').fetchall()
    conn.close()
    
    if len(notices) == 0:
        st.info("No notices posted yet. Be the first!")
    else:
        for notice in notices:
            if is_admin:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.success(notice['message'])
                with col2:
                    if st.button("🗑️", key=f"del_notice_{notice['id']}"):
                        conn = get_db_connection()
                        conn.execute('DELETE FROM notices WHERE id = ?', (notice['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
            else:
                st.success(notice['message'])

# --- RESOURCE VAULT PAGE ---
elif page == "Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Add past papers or notes to the database.")
    
    unit_code = st.text_input("Unit Code (e.g., STA 2101)")
    title = st.text_input("Resource Title (e.g., CAT 1 Past Paper)")
    uploaded_file = st.file_uploader("Upload file (PDF, DOCX)", type=["pdf", "docx"])
    
    if st.button("Save to Vault"):
        if unit_code and title and uploaded_file:
            file_bytes = uploaded_file.read()
            conn = get_db_connection()
            conn.execute('INSERT INTO resources (unit_code, title, file_name, file_data) VALUES (?, ?, ?, ?)', 
                         (unit_code, title, uploaded_file.name, file_bytes))
            conn.commit()
            conn.close()
            st.success(f"Saved {title} to database!")
            st.rerun()
        else:
            st.error("Please fill in all fields and upload a file.")
    
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
                if r['file_data'] is not None:
                    st.download_button(
                        label="⬇️ Download",
                        data=r['file_data'],
                        file_name=r['file_name'],
                        mime="application/pdf",
                        key=f"download_{r['id']}"
                    )
                else:
                    st.write("*(Re-upload needed)*")
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
    st.write("Ask questions about assignments, CATs, or anything stats-related!")
    
    if is_admin:
        if st.button("🗑️ Clear All Forum Questions"):
            conn = get_db_connection()
            conn.execute('DELETE FROM questions')
            conn.execute('DELETE FROM replies')
            conn.commit()
            conn.close()
            st.success("All questions cleared!")
            st.rerun()

    st.divider()

    # ASK A QUESTION (No forms, uses unique keys)
    st.subheader("Ask a Question")
    q_name = st.text_input("Your Name:", key="new_q_name")
    q_text = st.text_area("Your Question:", key="new_q_text")
    
    if st.button("Post Question", key="btn_post_q"):
        if q_name and q_text:
            conn = get_db_connection()
            conn.execute('INSERT INTO questions (name, question) VALUES (?, ?)', (q_name, q_text))
            conn.commit()
            conn.close()
            st.success("Question posted!")
            st.rerun()
        else:
            st.error("Please fill in both your name and the question.")

    st.divider()
    st.subheader("Recent Questions")
    
    conn = get_db_connection()
    questions = conn.execute('SELECT id, name, question, date FROM questions ORDER BY id DESC').fetchall()
    
    if len(questions) == 0:
        st.info("No questions yet. Ask the first one!")
    else:
        for q in questions:
            with st.container():
                if is_admin:
                    col1, col2 = st.columns([5, 1]) 
                    with col1:
                        st.markdown(f"**{q['name']}** asked: *{q['question']}*")
                        st.caption(f"Posted on {q['date']}")
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_q_{q['id']}"):
                            conn.execute('DELETE FROM replies WHERE question_id = ?', (q['id'],))
                            conn.execute('DELETE FROM questions WHERE id = ?', (q['id'],))
                            conn.commit()
                            st.rerun()
                else:
                    st.markdown(f"**{q['name']}** asked: *{q['question']}*")
                    st.caption(f"Posted on {q['date']}")

                # Display Replies
                replies = conn.execute('SELECT reply_name, reply, date FROM replies WHERE question_id = ?', (q['id'],)).fetchall()
                if replies:
                    for r in replies:
                        st.markdown(f"↳ 💬 **{r['reply_name']}** replied: {r['reply']}")
                
                # REPLY SECTION (Without forms, using columns)
                st.markdown("**Reply to this question:**")
                col_name, col_reply = st.columns([1, 3])
                with col_name:
                    r_name = st.text_input("Name", key=f"r_name_{q['id']}", label_visibility="collapsed", placeholder="Your Name")
                with col_reply:
                    r_text = st.text_input("Reply", key=f"r_text_{q['id']}", label_visibility="collapsed", placeholder="Write a reply...")
                
                if st.button("Submit Reply", key=f"btn_reply_{q['id']}"):
                    if r_name and r_text:
                        conn.execute('INSERT INTO replies (question_id, reply_name, reply) VALUES (?, ?, ?)', 
                                     (q['id'], r_name, r_text))
                        conn.commit()
                        st.rerun()
                    else:
                        st.error("Please enter both your name and a reply.")
                            
                st.divider()
    conn.close()

# --- LIVE CHAT PAGE ---
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
