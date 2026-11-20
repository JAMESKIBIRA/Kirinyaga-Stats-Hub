import streamlit as st
import sqlite3
import html
import re
import hmac
import hashlib
import os
import time
from contextlib import closing
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------- 1. CONFIG
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="✨",
                   layout="wide", initial_sidebar_state="auto")

EAT = timezone(timedelta(hours=3))  # Kenya time, no daylight saving
DB_FILE = "stats_hub_v6.db"
MAX_UPLOAD_MB = 15

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button, .stDownloadButton>button {
        border-radius: 12px; font-weight: 600; border: 1px solid #e0e0e0;
    }
    [data-testid="stSidebar"] .stButton>button {
        width: 100%; border-radius: 8px; text-align: left;
        padding: 10px 15px; margin-bottom: 5px; background-color: white;
    }
    .forum-card {
        background: white; padding: 18px; border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px;
        border-left: 5px solid #4A90E2; word-wrap: break-word;
    }
    .reply-text {
        background: #f1f3f5; padding: 10px 15px; border-radius: 10px;
        margin-top: 8px; font-size: 14px; word-wrap: break-word;
    }
    .meta { color: #868e96; font-size: 12px; }
    .tt-card {
        background: white; border-radius: 14px; padding: 14px 16px;
        margin-bottom: 12px; border-left: 5px solid #cbd5e1;
    }
    .tt-today { border-left-color: #4A90E2; background: #eef5ff; }
    .tt-day { font-weight: 700; font-size: 17px; margin-bottom: 4px; }
    .tt-slot { padding: 8px 0; border-top: 1px solid #eef0f2; font-size: 15px; }
    .tt-time { color: #2f6fba; font-weight: 600; font-size: 13px; }
    .tt-off { color: #868e96; padding-top: 4px; }
    .tt-badge {
        background: #4A90E2; color: white; border-radius: 8px;
        padding: 1px 8px; font-size: 12px; margin-left: 8px; font-weight: 600;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------- 2. DATABASE
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def q(sql, params=()):
    with closing(db()) as conn:
        return conn.execute(sql, params).fetchall()


def ex(sql, params=()):
    with closing(db()) as conn:
        conn.execute(sql, params)
        conn.commit()


def norm_unit(s):
    """'sta2344' / 'STA 2344' -> 'STA 2344'"""
    s = re.sub(r"\s+", "", s.strip().upper())
    m = re.match(r"^([A-Z]{2,4})(\d{3,4})$", s)
    return f"{m.group(1)} {m.group(2)}" if m else s


def init_db():
    with closing(db()) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS notices (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_code TEXT, title TEXT, file_name TEXT, file_data BLOB)")
        c.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, question TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, reply_name TEXT, reply TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reg_number TEXT UNIQUE)")
        c.execute("CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, reg_number TEXT, message TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        # Safe migrations: add new columns to the existing tables
        for table, col in [("notices", "posted_at TEXT"),
                           ("resources", "uploader TEXT"),
                           ("resources", "uploaded_at TEXT"),
                           ("questions", "reg_number TEXT"),
                           ("replies", "reg_number TEXT"),
                           ("students", "pin_hash TEXT"),
                           ("students", "pin_salt TEXT")]:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass  # column already exists
        # Normalise old unit codes (STA2344 -> STA 2344)
        for row in c.execute("SELECT id, unit_code FROM resources").fetchall():
            fixed = norm_unit(row["unit_code"] or "")
            if fixed != row["unit_code"]:
                conn.execute("UPDATE resources SET unit_code=? WHERE id=?", (fixed, row["id"]))
        conn.commit()


init_db()


# ------------------------------------------------------------- 3. HELPERS
def safe(text):
    """Escape user text so it can never inject HTML/JS into the page."""
    return html.escape(str(text)).replace("\n", "<br>")


def hash_pin(pin, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 100_000).hex()


def valid_pin(pin):
    return pin.isdigit() and 4 <= len(pin) <= 6


def norm_reg(s):
    return re.sub(r"\s+", "", s.strip().upper())


def mask_reg(reg):
    parts = reg.split("/")
    if len(parts) == 4:
        return f"{parts[0]}/{parts[1]}/•••••/{parts[3]}"
    return reg


def require_student():
    me = st.session_state.student
    if not me:
        st.info("🎓 Sign in from the sidebar (the » arrow, top-left) with your reg number and PIN.")
    return me


def go(page_name):
    st.session_state.page = page_name


# --------------------------------------------------- 4. SESSION + SIDEBAR
for key, default in [("is_admin", False), ("student", None), ("page", "🏠 Home"),
                     ("admin_fails", 0), ("admin_locked_until", 0.0), ("pin_fails", 0)]:
    if key not in st.session_state:
        st.session_state[key] = default

try:
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", None)
except Exception:
    ADMIN_PASSWORD = None

PAGES = ["🏠 Home", "📅 Timetable", "👥 Class Register", "📌 Notice Board",
         "📚 Resource Vault", "💬 Class Forum", "⚡ Live Chat"]

with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>✨ Stats Hub ✨</h1>", unsafe_allow_html=True)

    # ---- Student sign-in
    me = st.session_state.student
    if me:
        st.success(f"🎓 {me['name']}")
        if st.button("Sign out", key="btn_signout"):
            st.session_state.student = None
            st.rerun()
    else:
        with st.expander("🎓 Student sign-in"):
            si_reg = st.text_input("Reg number", key="si_reg", placeholder="PA100/G/28530/25")
            si_pin = st.text_input("PIN (4-6 digits)", type="password", key="si_pin")
            st.caption("First time? Register on the Class Register page. If you were added by the admin, "
                       "signing in the first time sets your PIN.")
            if st.button("Sign in", key="btn_signin"):
                row = q("SELECT * FROM students WHERE reg_number = ?", (norm_reg(si_reg),))
                if st.session_state.pin_fails >= 8:
                    st.error("Too many attempts. Reload the app and try again later.")
                elif not row:
                    st.error("Reg number not in the register. Register first.")
                else:
                    s = row[0]
                    if not valid_pin(si_pin):
                        st.error("PIN must be 4 to 6 digits.")
                    elif not s["pin_hash"]:
                        salt = os.urandom(8).hex()
                        ex("UPDATE students SET pin_hash=?, pin_salt=? WHERE id=?",
                           (hash_pin(si_pin, salt), salt, s["id"]))
                        st.session_state.student = {"name": s["name"], "reg": s["reg_number"]}
                        st.rerun()
                    elif hmac.compare_digest(hash_pin(si_pin, s["pin_salt"]), s["pin_hash"]):
                        st.session_state.student = {"name": s["name"], "reg": s["reg_number"]}
                        st.session_state.pin_fails = 0
                        st.rerun()
                    else:
                        st.session_state.pin_fails += 1
                        st.error("Wrong PIN.")

    # ---- Admin login (rate-limited, no hard-coded password)
    if not st.session_state.is_admin:
        with st.expander("🔐 Admin login"):
            if not ADMIN_PASSWORD:
                st.warning("Admin is disabled. Add ADMIN_PASSWORD to your Streamlit secrets.")
            else:
                password = st.text_input("Password", type="password", key="admin_pw")
                if st.button("Login", key="btn_admin_login"):
                    if time.time() < st.session_state.admin_locked_until:
                        st.error("Locked for a few minutes after too many attempts.")
                    elif hmac.compare_digest(password.encode(), str(ADMIN_PASSWORD).encode()):
                        st.session_state.is_admin = True
                        st.session_state.admin_fails = 0
                        st.rerun()
                    else:
                        st.session_state.admin_fails += 1
                        if st.session_state.admin_fails >= 5:
                            st.session_state.admin_locked_until = time.time() + 300
                            st.session_state.admin_fails = 0
                        st.error("Incorrect password.")
    else:
        st.success("👑 Admin mode")
        with st.expander("💾 Backup and restore"):
            st.caption("Streamlit Cloud can reset files on restart. Download a backup after big updates.")
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "rb") as f:
                    st.download_button("Download backup", f.read(), file_name="stats_hub_backup.db",
                                       key="dl_backup")
            restore = st.file_uploader("Restore from backup (.db)", type=["db"], key="restore_file")
            if restore is not None and st.button("Restore now", key="btn_restore"):
                data = restore.read()
                if data.startswith(b"SQLite format 3"):
                    with open(DB_FILE, "wb") as f:
                        f.write(data)
                    st.success("Restored.")
                    st.rerun()
                else:
                    st.error("That is not a valid database file.")
        if st.button("Logout", key="btn_admin_logout"):
            st.session_state.is_admin = False
            st.rerun()

    st.divider()
    for p in PAGES:
        if st.button(p, use_container_width=True, key=f"nav_{p}"):
            go(p)

page = st.session_state.page
is_admin = st.session_state.is_admin
me = st.session_state.student

# ------------------------------------------------------------------ HOME
if page == "🏠 Home":
    st.markdown("<h1 style='text-align: center;'>Welcome to the Kirinyaga Stats Hub! 📊</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>One place for BSc Statistics students at Kirinyaga University: timetable, notes, notices and class discussion. No more scrolling through WhatsApp.</p>", unsafe_allow_html=True)
    st.divider()

    latest = q("SELECT message, posted_at FROM notices ORDER BY id DESC LIMIT 1")
    if latest:
        st.info(f"📌 Latest notice: {latest[0]['message']}")
    elif is_admin:
        st.success("👑 Welcome back, Admin.")
    else:
        st.info("👋 Welcome! Check the timetable or ask a question in the forum.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📅 Timetable")
        st.write("Daily classes, venues and times, with today highlighted.")
        st.button("Open timetable", use_container_width=True, key="h1", on_click=go, args=("📅 Timetable",))
    with c2:
        st.markdown("### 📚 Resource Vault")
        st.write("Download past papers, notes and modules shared by the class.")
        st.button("Open vault", use_container_width=True, key="h2", on_click=go, args=("📚 Resource Vault",))
    with c3:
        st.markdown("### 💬 Class Forum")
        st.write("Ask questions and help classmates with answers.")
        st.button("Open forum", use_container_width=True, key="h3", on_click=go, args=("💬 Class Forum",))

    st.divider()
    st.subheader("🔗 Share the app")
    st.code("https://kirinyaga-stats-james.streamlit.app", language="text")

# ------------------------------------------------------------- TIMETABLE
elif page == "📅 Timetable":
    st.title("📅 Class Timetable")
    st.write("**Stage: Y2.S1 (August - December 2026/2027)**")

    TIMETABLE = {
        "Monday": [],
        "Tuesday": [
            ("7:00am - 10:00am", "STA 2243", "Fundamentals of Computer Interactive Stats", "LAB 1"),
            ("10:00am - 1:00pm", "SPM 2302", "Linear Algebra II", "JSM 105"),
        ],
        "Wednesday": [
            ("10:00am - 1:00pm", "SPM 2321", "Numerical Analysis I", "JSM 001"),
            ("1:00pm - 4:00pm", "STA 2344", "Intro to Epidemiological Methods", "LH 19"),
            ("4:00pm - 7:00pm", "STA 2342", "Calculus for Statistics III", "-"),
        ],
        "Thursday": [],
        "Friday": [
            ("10:00am - 1:00pm", "STA 2240", "Probability and Statistics II", "JSM 101"),
        ],
    }
    today = datetime.now(EAT).strftime("%A")

    for day, slots in TIMETABLE.items():
        cls = "tt-card tt-today" if day == today else "tt-card"
        badge = "<span class='tt-badge'>Today</span>" if day == today else ""
        parts = [f"<div class='{cls}'><div class='tt-day'>{day}{badge}</div>"]
        if not slots:
            parts.append("<div class='tt-off'>No lectures 😴</div>")
        for time_str, code, name, venue in slots:
            venue_txt = venue if venue != "-" else "Venue to be confirmed"
            parts.append(
                f"<div class='tt-slot'><div class='tt-time'>{time_str}</div>"
                f"<b>{code}</b> · {name}<br><span class='meta'>📍 {venue_txt}</span></div>"
            )
        parts.append("</div>")
        st.markdown("".join(parts), unsafe_allow_html=True)

# -------------------------------------------------------- CLASS REGISTER
elif page == "👥 Class Register":
    st.title("👥 Class Register")
    st.write("Official list of students in the BSc Statistics class.")

    with st.expander("➕ Add yourself to the register"):
        with st.form("self_register", clear_on_submit=True):
            n = st.text_input("Full name")
            r = st.text_input("Registration number", placeholder="PA100/G/28530/25")
            p = st.text_input("Choose a PIN (4-6 digits)", type="password",
                              help="You will use it to sign in and post. Keep it private.")
            if st.form_submit_button("Join the register"):
                reg = norm_reg(r)
                if not (n.strip() and reg):
                    st.error("Enter your name and reg number.")
                elif not re.match(r"^[A-Z0-9]+/[A-Z]/\d+/\d{2}$", reg):
                    st.error("Reg number format looks wrong. Example: PA100/G/28530/25")
                elif not valid_pin(p):
                    st.error("PIN must be 4 to 6 digits.")
                else:
                    salt = os.urandom(8).hex()
                    try:
                        ex("INSERT INTO students (name, reg_number, pin_hash, pin_salt) VALUES (?,?,?,?)",
                           (n.strip().upper()[:80], reg, hash_pin(p, salt), salt))
                        st.success("You're in! Sign in from the sidebar to post.")
                    except sqlite3.IntegrityError:
                        st.error("That reg number is already registered.")

    total = q("SELECT COUNT(*) AS n FROM students")[0]["n"]
    st.markdown(f"### 🎓 Total registered students: **{total}**")
    search = st.text_input("🔍 Search by name or reg number:", key="search_student")

    if search:
        like = f"%{search.strip()}%"
        students = q("SELECT id, name, reg_number FROM students WHERE name LIKE ? OR reg_number LIKE ? ORDER BY name",
                     (like, like))
    else:
        students = q("SELECT id, name, reg_number FROM students ORDER BY name")

    st.divider()
    if not students:
        st.warning(f"No student matches '{search}'.") if search else st.info("The register is empty. Be the first to join.")
    for s in students:
        if is_admin:
            c1, c2, c3, c4 = st.columns([4, 4, 1, 1])
            c1.write(s["name"])
            c2.write(s["reg_number"])
            if c3.button("🔑", key=f"pin_{s['id']}", help="Reset PIN"):
                ex("UPDATE students SET pin_hash=NULL, pin_salt=NULL WHERE id=?", (s["id"],))
                st.toast("PIN reset. The student sets a new one on next sign-in.")
            if c4.button("🗑️", key=f"del_student_{s['id']}", help="Remove student"):
                ex("DELETE FROM students WHERE id=?", (s["id"],))
                st.rerun()
        else:
            st.write(f"{s['name']} · {mask_reg(s['reg_number'])}")

# ----------------------------------------------------------- NOTICE BOARD
elif page == "📌 Notice Board":
    st.title("📌 Notice Board")

    if is_admin:
        with st.form("post_notice", clear_on_submit=True):
            text = st.text_area("Post a notice 📢")
            if st.form_submit_button("Post notice 🚀"):
                if text.strip():
                    ex("INSERT INTO notices (message, posted_at) VALUES (?, ?)",
                       (text.strip()[:1000], datetime.now(EAT).strftime("%d %b %Y")))
                    st.rerun()
                else:
                    st.warning("Write something first.")
        st.divider()

    notices = q("SELECT id, message, posted_at FROM notices ORDER BY id DESC")
    if not notices:
        st.info("No notices yet.")
    for n in notices:
        c1, c2 = st.columns([6, 1]) if is_admin else (st.container(), None)
        with c1:
            st.success(n["message"])
            if n["posted_at"]:
                st.caption(n["posted_at"])
        if is_admin and c2.button("🗑️", key=f"del_notice_{n['id']}"):
            ex("DELETE FROM notices WHERE id=?", (n["id"],))
            st.rerun()

# --------------------------------------------------------- RESOURCE VAULT
elif page == "📚 Resource Vault":
    st.title("📚 Resource Vault")
    st.write("Past papers, notes and modules shared by the class.")

    with st.expander("➕ Upload a resource"):
        if require_student():
            with st.form("upload_res", clear_on_submit=True):
                unit_code = st.text_input("Unit code", placeholder="STA 2344")
                title = st.text_input("Title", placeholder="CAT 1 2026")
                up = st.file_uploader("File (PDF or DOCX)", type=["pdf", "docx"])
                if st.form_submit_button("Save to vault 💾"):
                    if not (unit_code.strip() and title.strip() and up):
                        st.error("Fill in every field and choose a file.")
                    else:
                        data = up.read()
                        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
                            st.error(f"File is too large. The limit is {MAX_UPLOAD_MB} MB.")
                        else:
                            ex("INSERT INTO resources (unit_code, title, file_name, file_data, uploader, uploaded_at) "
                               "VALUES (?,?,?,?,?,?)",
                               (norm_unit(unit_code), title.strip()[:120], up.name, data,
                                me["name"], datetime.now(EAT).strftime("%d %b %Y")))
                            st.success("Saved to the vault 🎉")
                            st.rerun()

    st.divider()
    units = [r["unit_code"] for r in q("SELECT DISTINCT unit_code FROM resources ORDER BY unit_code")]
    f1, f2 = st.columns(2)
    unit_filter = f1.selectbox("Unit", ["All units"] + units)
    text_text_filter = f2.text_input("Search title")

    sql = "SELECT id, unit_code, title, file_name, uploader, uploaded_at FROM resources WHERE 1=1"
    params = []
    if unit_filter != "All units":
        sql += " AND unit_code = ?"
        params.append(unit_filter)
    if text_filter.strip():
        sql += " AND title LIKE ?"
        params.append(f"%{text_filter.strip()}%")
    resources = q(sql + " ORDER BY id DESC", tuple(params))

    if not resources:
        st.info("Nothing here yet. Upload the first resource.")
    for r in resources:
        with st.container(border=True):
            st.markdown(f"**{r['unit_code']}** · {r['title']}")
            by = r["uploader"] or "Unknown"
            st.caption(f"Shared by {by}" + (f" on {r['uploaded_at']}" if r["uploaded_at"] else ""))
            a, b = st.columns([2, 1])
            with a:
                # File data loads only when asked, so the page stays fast on mobile data
                if st.session_state.get(f"prep_{r['id']}"):
                    blob = q("SELECT file_data FROM resources WHERE id=?", (r["id"],))[0]["file_data"]
                    mime = ("application/pdf" if r["file_name"].lower().endswith(".pdf")
                            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    st.download_button("⬇️ Download", data=blob, file_name=r["file_name"],
                                       mime=mime, key=f"dl_{r['id']}")
                elif st.button("📄 Get file", key=f"get_{r['id']}"):
                    st.session_state[f"prep_{r['id']}"] = True
                    st.rerun()
            with b:
                if is_admin and st.button("🗑️", key=f"del_res_{r['id']}"):
                    ex("DELETE FROM resources WHERE id=?", (r["id"],))
                    st.rerun()

# ------------------------------------------------------------ CLASS FORUM
elif page == "💬 Class Forum":
    st.title("💬 Class Q&A Forum")
    st.write("Ask questions, share answers, and help the squad out. 🤝")

    if is_admin:
        confirm = st.checkbox("I want to delete ALL questions and replies", key="confirm_clear")
        if st.button("🗑️ Clear all", key="btn_clear_all", disabled=not confirm):
            ex("DELETE FROM replies")
            ex("DELETE FROM questions")
            st.rerun()

    st.divider()
    if require_student():
        with st.form("post_q", clear_on_submit=True):
            q_text = st.text_area("What's your question?", placeholder="Type here...")
            if st.form_submit_button("Post question 🚀"):
                if q_text.strip():
                    ex("INSERT INTO questions (name, question, reg_number) VALUES (?,?,?)",
                       (me["name"], q_text.strip()[:2000], me["reg"]))
                    st.rerun()
                else:
                    st.warning("Write your question first.")

    st.divider()
    limit = st.session_state.get("q_limit", 15)
    questions = q("SELECT id, name, question, date FROM questions ORDER BY id DESC LIMIT ?", (limit + 1,))
    has_more = len(questions) > limit
    if not questions:
        st.info("No questions yet. Ask the first one! 👀")

    for ques in questions[:limit]:
        st.markdown(
            f"<div class='forum-card'>🗣️ <b>{safe(ques['name'])}</b> asked:"
            f"<br>{safe(ques['question'])}"
            f"<div class='meta'>{str(ques['date'])[:10]}</div></div>",
            unsafe_allow_html=True)

        for rep in q("SELECT reply_name, reply FROM replies WHERE question_id=? ORDER BY id", (ques["id"],)):
            st.markdown(f"<div class='reply-text'>↳ 💬 <b>{safe(rep['reply_name'])}</b>: {safe(rep['reply'])}</div>",
                        unsafe_allow_html=True)

        with st.expander("Reply 👇"):
            if me:
                with st.form(f"reply_form_{ques['id']}", clear_on_submit=True):
                    r_text = st.text_area("Your reply", key=f"r_text_{ques['id']}")
                    if st.form_submit_button("Reply 💬"):
                        if r_text.strip():
                            ex("INSERT INTO replies (question_id, reply_name, reply, reg_number) VALUES (?,?,?,?)",
                               (ques["id"], me["name"], r_text.strip()[:2000], me["reg"]))
                            st.rerun()
                        else:
                            st.warning("Write a reply first.")
            else:
                st.caption("Sign in from the sidebar to reply.")
            if is_admin and st.button("🗑️ Delete question", key=f"del_q_{ques['id']}"):
                ex("DELETE FROM replies WHERE question_id=?", (ques["id"],))
                ex("DELETE FROM questions WHERE id=?", (ques["id"],))
                st.rerun()

    if has_more and st.button("Load more", key="q_more"):
        st.session_state.q_limit = limit + 15
        st.rerun()

# -------------------------------------------------------------- LIVE CHAT
elif page == "⚡ Live Chat":
    st.title("⚡ Live Chat Room")
    st.write("Chat with the class. New messages appear every few seconds.")

    if is_admin and st.button("🗑️ Clear chat history", type="primary", key="btn_clear_chat"):
        ex("DELETE FROM chat")
        st.rerun()

    st.divider()

    def show_messages():
        rows = q("SELECT name, reg_number, message FROM (SELECT * FROM chat ORDER BY id DESC LIMIT 50) ORDER BY id")
        if not rows:
            st.info("No messages yet. Say hi 👋")
        for m in rows:
            mine = bool(me) and m["reg_number"] == me["reg"]
            with st.chat_message("user" if mine else "assistant"):
                st.markdown(f"**{safe(m['name'])}**", unsafe_allow_html=True)
                st.markdown(safe(m["message"]), unsafe_allow_html=True)

    if hasattr(st, "fragment"):
        st.fragment(run_every=5)(show_messages)()
    else:
        show_messages()
        st.button("🔄 Refresh", key="chat_refresh")

    if me:
        if prompt := st.chat_input("Type your message here..."):
            ex("INSERT INTO chat (name, reg_number, message) VALUES (?,?,?)",
               (me["name"], me["reg"], prompt.strip()[:500]))
            st.rerun()
    else:
        require_student()
