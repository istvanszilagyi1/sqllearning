import streamlit as st
import sqlite3
import pandas as pd
import csv
from datetime import datetime
import os

# --- CONFIG ---
TEACHER_PASSWORD = "sql2025"  # <-- Itt állítsd be a saját jelszavad!

# --- Page setup ---
st.set_page_config(
    page_title="SQL Training App",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Page background */
    .stApp {
        background-color: #f5f5f5;  /* Világos szürke háttér */
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #333333;  /* Sötétszürke sidebar */
        color: white;
    }
    /* Buttons */
    .stButton>button {
        background-color: #ffcc00;  /* Veeva sárga */
        color: black;
        font-weight: bold;
    }
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #333333;  /* Sötétszürke címsorok */
    }
    /* Inputs, text areas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border: 2px solid #ffcc00;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Interactive SQL Training App")
st.write("Students: Enter your name, complete the SQL task, and run your query. Results are logged automatically.")

# --- Session state ---
if "score" not in st.session_state:
    st.session_state.score = 0
if "name" not in st.session_state:
    st.session_state.name = ""

# --- Mode selection ---
mode = st.sidebar.radio("Mode", ["Student", "Teacher"])

# ==================== STUDENT MODE ====================
if mode == "Student":

    name = st.text_input("Your name:", st.session_state.name)
    if name:
        st.session_state.name = name

    st.divider()

    # --- Create in-memory SQLite database ---
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department TEXT,
        salary INTEGER,
        hire_date DATE
    )
    """)

    cursor.executemany("INSERT INTO employees (name, department, salary, hire_date) VALUES (?, ?, ?, ?)", [
        ("Anna Kovacs", "HR", 400000, "2020-02-10"),
        ("Peter Nagy", "IT", 650000, "2018-05-03"),
        ("Eszter Toth", "Marketing", 520000, "2021-11-11"),
        ("Marton Szabo", "IT", 720000, "2019-09-21"),
        ("Julia Farkas", "HR", 450000, "2022-03-05"),
    ])
    conn.commit()

    # --- Sidebar info ---
    st.sidebar.header("Database Schema")
    st.sidebar.markdown("""
    **Table:** employees  
    - id: integer, primary key  
    - name: text  
    - department: text  
    - salary: integer  
    - hire_date: date  
    """)

    # --- Task ---
    st.subheader("🧠 Task")
    st.write("**Task 1:** List all employees from the table.")
    expected_query = "SELECT * FROM employees;"

    # --- SQL input ---
    st.subheader("💻 Your SQL Query")
    default_query = "SELECT * FROM employees;"
    sql_query = st.text_area("Write your SQL query here:", value=default_query, height=150)

    # --- CSV log function ---
    def log_submission(name, query, correct, score):
        file_exists = os.path.isfile("submissions.csv")
        with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "name", "task", "query", "correct", "score"])
            writer.writerow([datetime.now().isoformat(), name, "Task 1", query, correct, score])

    # --- Run Query button ---
    if st.button("Run Query"):
        try:
            df = pd.read_sql_query(sql_query, conn)
            st.success("✅ Query executed successfully!")
            st.dataframe(df, use_container_width=True)

            # Optional chart
            numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
            if len(numeric_cols) > 0:
                st.subheader("📊 Visualization")
                st.bar_chart(df[numeric_cols])

            # Compare with expected
            expected_df = pd.read_sql_query(expected_query, conn)
            if df.equals(expected_df):
                st.success(f"🎉 Correct answer, {st.session_state.name}! +1 point")
                st.session_state.score += 1
                correct = True
            else:
                st.info("❌ Not the expected result. Try again!")
                correct = False

            log_submission(st.session_state.name, sql_query, correct, st.session_state.score)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

    # --- Score ---
    st.divider()
    st.subheader(f"🏅 Current Score for {name}: {st.session_state.score}")

else:
    st.subheader("🔐 Teacher Dashboard")
    password = st.text_input("Enter teacher password:", type="password")

    if password == TEACHER_PASSWORD:
        st.success("Access granted. Welcome, teacher!")

        if os.path.exists("submissions.csv"):
            df = pd.read_csv("submissions.csv")
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ Download submissions (CSV)", df.to_csv(index=False).encode("utf-8"), file_name="submissions.csv")
        else:
            st.info("No submissions yet.")
    elif password:
        st.error("Incorrect password.")
