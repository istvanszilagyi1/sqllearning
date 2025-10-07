import streamlit as st
import sqlite3
import pandas as pd
import csv
from datetime import datetime
import os

# --- CONFIG ---
TEACHER_PASSWORD = "sql2025"

# --- Page setup ---
st.set_page_config(page_title="SQL Training App", layout="wide")

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

    # --- Create tables ---
    cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department_id INTEGER,
        salary INTEGER,
        hire_date DATE
    )
    """)
    cursor.execute("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        manager TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        product TEXT,
        amount INTEGER,
        sale_date DATE
    )
    """)
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        country TEXT,
        industry TEXT
    )
    """)

    # --- Insert sample data ---
    cursor.executemany("INSERT INTO departments (name, manager) VALUES (?, ?)", [
        ("HR", "Anna Kovacs"),
        ("IT", "Peter Nagy"),
        ("Marketing", "Eszter Toth")
    ])
    cursor.executemany("INSERT INTO employees (name, department_id, salary, hire_date) VALUES (?, ?, ?, ?)", [
        ("Anna Kovacs", 1, 400000, "2020-02-10"),
        ("Peter Nagy", 2, 650000, "2018-05-03"),
        ("Eszter Toth", 3, 520000, "2021-11-11"),
        ("Marton Szabo", 2, 720000, "2019-09-21"),
        ("Julia Farkas", 1, 450000, "2022-03-05")
    ])
    cursor.executemany("INSERT INTO sales (employee_id, product, amount, sale_date) VALUES (?, ?, ?, ?)", [
        (2, "Product A", 10000, "2023-01-10"),
        (3, "Product B", 15000, "2023-01-12"),
        (4, "Product A", 20000, "2023-01-15")
    ])
    cursor.executemany("INSERT INTO customers (name, country, industry) VALUES (?, ?, ?)", [
        ("Acme Corp", "Hungary", "IT"),
        ("Beta Ltd", "Germany", "Marketing")
    ])
    conn.commit()

    # --- Sidebar info ---
    st.sidebar.header("Database Schema")
    st.sidebar.markdown("""
    **Tables:**  
    - employees(id, name, department_id, salary, hire_date)  
    - departments(id, name, manager)  
    - sales(id, employee_id, product, amount, sale_date)  
    - customers(id, name, country, industry)  
    """)

    # --- Tasks list (story + tip + expected query) ---
    tasks = [
        {
            "story": "🕵️‍♀️ You are the new HR detective at Veeva Systems. First, let's get to know all the employees in the company. Peek at their names, departments, and salaries. It's like reading a fun staff directory!",
            "tip": "Use SELECT to choose which columns you want to see.",
            "task": "List all employees with their name, department_id, and salary.",
            "expected": "SELECT * FROM employees;"
        },
        {
            "story": "💼 The IT manager is curious who's earning more than 600,000 HUF. It's like a treasure hunt for the high-salary heroes!",
            "tip": "Use WHERE to filter rows by a condition.",
            "task": "List all IT employees with salary greater than 600,000.",
            "expected": "SELECT * FROM employees WHERE department_id=2 AND salary>600000;"
        },
        {
            "story": "📅 HR wants to send welcome emails to the newest recruits. Let's sort the employees by hire date, newest first. Imagine a 'Welcome Party' queue!",
            "tip": "Use ORDER BY to sort results ascending (ASC) or descending (DESC).",
            "task": "List all employees ordered by hire_date descending.",
            "expected": "SELECT * FROM employees ORDER BY hire_date DESC;"
        },
        {
            "story": "🏢 The CEO is counting how many employees are in each department. Let's group them like collecting jellybeans in jars by color!",
            "tip": "Use GROUP BY to group rows and COUNT() to count them.",
            "task": "Count the number of employees per department.",
            "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id;"
        }
    ]

    # --- Iterate through tasks ---
    for idx, t in enumerate(tasks, 1):
        st.subheader(f"🧠 Task {idx}")
        st.markdown(f"**Story:** {t['story']}")
        st.markdown(f"**SQL Tip:** {t['tip']}")
        st.markdown(f"**Task:** {t['task']}")

        default_query = t["expected"]
        sql_query = st.text_area(f"Write your SQL query for Task {idx}:", value=default_query, height=120, key=f"task_{idx}")

        if st.button(f"Run Task {idx} Query", key=f"run_{idx}"):
            try:
                df = pd.read_sql_query(sql_query, conn)
                st.success("✅ Query executed successfully!")
                st.dataframe(df, use_container_width=True)

                numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
                if len(numeric_cols) > 0:
                    st.subheader("📊 Visualization")
                    st.bar_chart(df[numeric_cols])

                expected_df = pd.read_sql_query(t["expected"], conn)
                if df.equals(expected_df):
                    st.success(f"🎉 Correct answer, {st.session_state.name}! +1 point")
                    st.session_state.score += 1
                    correct = True
                else:
                    st.info("❌ Not the expected result. Try again!")
                    correct = False

                # log CSV
                file_exists = os.path.isfile("submissions.csv")
                with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["timestamp", "name", "task", "query", "correct", "score"])
                    writer.writerow([datetime.now().isoformat(), st.session_state.name, f"Task {idx}", sql_query, correct, st.session_state.score])

            except Exception as e:
                st.error(f"⚠️ Error: {e}")

    st.divider()
    st.subheader(f"🏅 Current Score for {st.session_state.name}: {st.session_state.score}")

# ==================== TEACHER MODE ====================
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
