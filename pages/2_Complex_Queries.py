import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import csv
import graphviz

# --- CONFIG ---
TEACHER_PASSWORD = "sql2025"

# --- PAGE SETUP ---
st.set_page_config(page_title="Advanced SQL Learning App", layout="wide")

st.title("🧩 Advanced SQL Learning Platform")
st.write("""
Welcome to the interactive SQL learning app!  
Choose your mode on the left, and explore **joins**, **subqueries**, and **aggregations** step-by-step.
""")

# ======================== ER DIAGRAM ========================
with st.expander("📊 Show ER Diagram"):
    dot = graphviz.Digraph()
    dot.attr("node", shape="box", style="rounded,filled", color="#E0E0E0", fillcolor="#F8F8F8")

    dot.node("departments", "departments\n- id (PK)\n- name\n- manager")
    dot.node("employees", "employees\n- id (PK)\n- name\n- department_id (FK)\n- salary\n- hire_date")
    dot.node("projects", "projects\n- id (PK)\n- name\n- budget\n- department_id (FK)")
    dot.node("tasks", "tasks\n- id (PK)\n- project_id (FK)\n- assigned_to (FK)\n- hours\n- status")

    dot.edge("departments", "employees", label="1 → many")
    dot.edge("departments", "projects", label="1 → many")
    dot.edge("projects", "tasks", label="1 → many")
    dot.edge("employees", "tasks", label="1 → many (via assigned_to)")

    st.graphviz_chart(dot, use_container_width=True)

# ======================== MODE SELECTION ========================
mode = st.sidebar.radio("Mode", ["Student", "Teacher"])

# ======================== STUDENT MODE ========================
if mode == "Student":
    name = st.text_input("Your name:")
    if not name:
        st.warning("Please enter your name to begin.")
        st.stop()

    # --- Database setup ---
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        manager TEXT
    );
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department_id INTEGER,
        salary INTEGER,
        hire_date DATE,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    );
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        budget INTEGER,
        department_id INTEGER,
        FOREIGN KEY(department_id) REFERENCES departments(id)
    );
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        assigned_to INTEGER,
        hours INTEGER,
        status TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(assigned_to) REFERENCES employees(id)
    );
    """)

    cursor.executemany("INSERT INTO departments (name, manager) VALUES (?, ?)", [
        ("IT", "Peter Nagy"),
        ("HR", "Anna Kovacs"),
        ("Marketing", "Eszter Toth")
    ])
    cursor.executemany("INSERT INTO employees (name, department_id, salary, hire_date) VALUES (?, ?, ?, ?)", [
        ("Adam Kiss", 1, 800000, "2020-01-10"),
        ("Julia Farkas", 2, 500000, "2021-06-03"),
        ("Robert Toth", 3, 450000, "2019-11-17")
    ])
    cursor.executemany("INSERT INTO projects (name, budget, department_id) VALUES (?, ?, ?)", [
        ("Website Redesign", 1200000, 1),
        ("Recruitment Drive", 400000, 2),
        ("Ad Campaign", 900000, 3)
    ])
    cursor.executemany("INSERT INTO tasks (project_id, assigned_to, hours, status) VALUES (?, ?, ?, ?)", [
        (1, 1, 50, "Done"),
        (1, 1, 30, "In Progress"),
        (2, 2, 25, "Done"),
        (3, 3, 40, "In Progress")
    ])
    conn.commit()

    # --- TASK TYPES ---
    task_types = {
        "JOINs": [
            {
                "title": "Simple INNER JOIN",
                "explanation": "An INNER JOIN returns rows with matching values in both tables.",
                "visual": "A ∩ B (intersection)",
                "story": "Show project names with their department managers.",
                "expected": "SELECT p.name AS project, d.manager FROM projects p JOIN departments d ON p.department_id = d.id;"
            },
            {
                "title": "LEFT JOIN",
                "explanation": "A LEFT JOIN returns all rows from the left table, even if there’s no match on the right.",
                "visual": "A ⟕ B",
                "story": "List all departments and their projects (even those without projects).",
                "expected": "SELECT d.name AS department, p.name AS project FROM departments d LEFT JOIN projects p ON d.id = p.department_id;"
            }
        ],
        "Subqueries": [
            {
                "title": "Basic Subquery",
                "explanation": "A subquery allows using the result of another query inside a WHERE clause.",
                "visual": "Filter rows by nested query result.",
                "story": "List employees working in departments with projects over 1,000,000 budget.",
                "expected": "SELECT name FROM employees WHERE department_id IN (SELECT department_id FROM projects WHERE budget > 1000000);"
            }
        ],
        "Aggregations": [
            {
                "title": "GROUP BY and HAVING",
                "explanation": "Use GROUP BY to group rows, and HAVING to filter groups.",
                "visual": "Σ grouped results.",
                "story": "Show departments where average salary exceeds 600,000.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id HAVING AVG(salary) > 600000;"
            }
        ]
    }

    # --- Task Type Selection ---
    task_type = st.sidebar.selectbox("Choose Task Type", list(task_types.keys()))

    if "task_index" not in st.session_state:
        st.session_state.task_index = 0

    tasks = task_types[task_type]
    task = tasks[st.session_state.task_index]

    st.subheader(f"📘 {task_type} – {task['title']}")
    st.markdown(f"**Explanation:** {task['explanation']}")
    st.caption(f"🌀 Visualization: {task['visual']}")
    st.info(task["story"])

    sql_query = st.text_area("✍️ Write your SQL query:")

    # --- Navigation ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous Task"):
            if st.session_state.task_index > 0:
                st.session_state.task_index -= 1
                st.rerun()
    with col2:
        if st.button("Next Task ➡️"):
            if st.session_state.task_index < len(tasks)-1:
                st.session_state.task_index += 1
                st.rerun()

    # --- Logging ---
    def log_submission(name, query, correct, score, task_type, task_index):
        file_exists = os.path.isfile("submissions.csv")
        with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "name", "category", "task_index", "query", "correct", "score"])
            writer.writerow([datetime.now().isoformat(), name, task_type, task_index, query, correct, score])

    # --- Run Query ---
    if st.button("▶️ Run Query"):
        try:
            df = pd.read_sql_query(sql_query, conn)
            st.success("✅ Query executed successfully!")
            st.dataframe(df, use_container_width=True)

            expected_df = pd.read_sql_query(task["expected"], conn)
            if df.equals(expected_df):
                st.success(f"🎉 Correct answer, {name}!")
                correct = True
                score = 1
            else:
                st.warning("❌ Not quite right — check your JOINs or GROUP BY.")
                correct = False
                score = 0

            log_submission(name, sql_query, correct, score, task_type, st.session_state.task_index)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

# ======================== TEACHER MODE ========================
else:
    st.subheader("🔐 Teacher Dashboard")
    password = st.text_input("Enter teacher password:", type="password")

    if password == TEACHER_PASSWORD:
        st.success("Access granted. Welcome, teacher! 👩‍🏫")

        if os.path.exists("submissions.csv"):
            try:
                df = pd.read_csv("submissions.csv", encoding="utf-8", on_bad_lines="skip")
                st.dataframe(df, use_container_width=True)
                st.download_button("⬇️ Download all submissions", df.to_csv(index=False).encode("utf-8"), "submissions.csv")
            except Exception as e:
                st.error(f"⚠️ Error reading CSV: {e}")
        else:
            st.info("No submissions yet.")
    elif password:
        st.error("Incorrect password.")
