import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Kirinyaga Stats Hub", page_icon="🎓", layout="wide")

# 2. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Timetable", "Notice Board"])

# 3. Home Page
if page == "Home":
    st.title("Welcome to the Kirinyaga Stats Hub! 🎓")
    st.write("This is a central platform for all BSc Statistics students at Kirinyaga University.")
    st.write("Use the sidebar to check your timetable, read notices, and stay updated.")
    st.info("Built by James Kiruma using Python and Streamlit.")

# 4. Timetable Page
elif page == "Timetable":
    st.title("🗓️ Class Timetable")
    st.write("Here is the schedule for this semester.")
    
    # Creating the timetable data
    timetable_data = {
        "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "8:00 AM - 10:00 AM": ["Calculus III", "Probability II", "Epidemiology", "Linear Algebra II", "Calculus III"],
        "10:00 AM - 12:00 PM": ["Linear Algebra II", "Calculus III", "Probability II", "Epidemiology", "Stats Computing"],
        "2:00 PM - 4:00 PM": ["Epidemiology", "Stats Computing", "Calculus III", "Probability II", "Linear Algebra II"]
    }
    
    df = pd.DataFrame(timetable_data)
    st.dataframe(df, use_container_width=True)

# 5. Notice Board Page
elif page == "Notice Board":
    st.title("📢 Notice Board")
    st.write("Latest updates for the class.")
    
    st.success("📌 **Update (Nov 14):** CAT results for Linear Algebra II are expected next week.")
    st.warning("📌 **Reminder:** Submit your Stats Computing assignment by Friday.")
    st.info("📌 **Event:** Departmental seminar coming up on Nov 20th.")
