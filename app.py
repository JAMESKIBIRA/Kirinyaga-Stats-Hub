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

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Timetable", "Notice Board", "Resource Vault", "Class Forum", "Live Chat"])

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
    st.dataframe(df, width="stretch")

# --- NOTICE BOARD PAGE ---
elif page == "Notice Board":
    st.title("📌 Notice Board")
    
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
        df_resources = pd.DataFrame([dict(r) for r in resources])
        st.dataframe(df_resources, width="stretch")

# --- CLASS FORUM PAGE ---
elif page == "Class Forum":
    st.title("💬 Class Q&A Forum")
    st.write("Ask questions about assignments, CATs, or anything stats-related!")
    
    with st.form("ask_form", clear_on_submit=True):
        name = st.text_input("Your Name (or nickname):")
        question = st.text_area("Your Question:")
        submit_q = st.form_submit_button("Post Question")
        
        if submit_q and name and question:
            conn = get_db_connection()
            conn.execute('INSERT INTO questions (name, question) VALUES (?, ?)', (name, question))
            conn.commit()
            conn.close()
            st.success("Question posted!")
            st.rerun()
            
    st.divider()
    st.subheader("Recent Questions")
    
    conn = get_db_connection()
    questions = conn.execute('SELECT id, name, question, date FROM questions ORDER BY id DESC').fetchall()
    
    if len(questions) == 0:
        st.info("No questions yet. Ask the first one!")
    else:
        for q in questions:
            with st.container():
                st.markdown(f"**{q['name']}** asked: *{q['question']}*")
                st.caption(f"Posted on {q['date']}")
                
                replies = conn.execute('SELECT reply, date FROM replies WHERE question_id = ?', (q['id'],)).fetchall()
                if replies:
                    for r in replies:
                        st.markdown(f"↳ 💬 {r['reply']}")
                
                with st.form(f"reply_form_{q['id']}"):
                    reply_text = st.text_input("Write a reply...", key=f"reply_{q['id']}")
                    submit_reply = st.form_submit_button("Reply")
                    if submit_reply and reply_text:
                        conn.execute('INSERT INTO replies (question_id, reply) VALUES (?, ?)', (q['id'], reply_text))
                        conn.commit()
                        st.rerun()
                st.divider()
    conn.close()

# --- LIVE CHAT PAGE ---
elif page == "Live Chat":
    st.title("⚡ Live Chat Room")
    st.write("Chat with classmates in real-time.")
    
    # NEW: Button to clear the chat messages
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
