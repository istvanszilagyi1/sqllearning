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
st.set_page_config(page_title="Advanced SQL Queries", layout="wide")

st.title("🧩 Advanced SQL Queries – Lesson 2")
st.write("""
In this lesson, we’ll explore **multi-table joins**, **aggregations**, and **subqueries**.  
Before starting, check the ER diagram below to see how the database tables connect.
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

    # --- Tasks ---
    tasks = [
        {
            "story": "💼 The company wants to see which **manager** is responsible for which **project**.",
            "tip": "Hint: JOIN projects → departments using department_id.",
            "task": "Show project name and department manager.",
            "expected": "SELECT p.name AS project, d.manager FROM projects p JOIN departments d ON p.department_id = d.id;"
        },
        {
            "story": "💰 Management needs to find employees working in departments with **projects over 1M budget**.",
            "tip": "Hint: Use a subquery in WHERE to match department IDs.",
            "task": "List employee names whose department has projects > 1,000,000.",
            "expected": "SELECT name FROM employees WHERE department_id IN (SELECT department_id FROM projects WHERE budget > 1000000);"
        },
        {
            "story": "⏱️ HR wants to calculate how many **total hours** each employee worked.",
            "tip": "Hint: JOIN tasks and employees, then GROUP BY employee.",
            "task": "List employee names and total hours spent on tasks.",
            "expected": "SELECT e.name, SUM(t.hours) AS total_hours FROM employees e JOIN tasks t ON e.id = t.assigned_to GROUP BY e.name;"
        },
        {
            "story": "✅ The manager wants to see employees who **completed all their tasks**.",
            "tip": "Hint: Use a subquery counting only 'Done' tasks.",
            "task": "Show names of employees with all tasks marked as Done.",
            "expected": "SELECT e.name FROM employees e WHERE e.id NOT IN (SELECT assigned_to FROM tasks WHERE status != 'Done');"
        },
        {
            "story": "📈 Finance needs to find departments with **average salary** above 600,000.",
            "tip": "Hint: Use GROUP BY + HAVING.",
            "task": "List department_id and AVG(salary) where AVG > 600000.",
            "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id HAVING AVG(salary) > 600000;"
        }
    ]

    # --- Task selection ---
    st.sidebar.header("📘 Select Task")
    task_index = st.sidebar.number_input("Task number", 0, len(tasks)-1, 0)
    task = tasks[task_index]

    st.subheader(f"🧠 Task {task_index+1}")
    st.markdown(f"**Story:** {task['story']}")
    st.markdown(f"**Tip:** {task['tip']}")
    st.markdown(f"**Your task:** {task['task']}")

    sql_query = st.text_area("Write your SQL query here:")

    # --- Logging function ---
    def log_submission(name, query, correct, score, task_index):
        file_exists = os.path.isfile("submissions.csv")
        with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "name", "lesson", "task_index", "query", "correct", "score"])
            writer.writerow([datetime.now().isoformat(), name, "Complex Queries", task_index, query, correct, score])

    # --- Run query ---
    if st.button("Run Query"):
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

            log_submission(name, sql_query, correct, score, task_index)

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

                # Filter for this lesson only
                lesson_df = df[df["lesson"] == "Complex Queries"]
                st.markdown("### 📊 Complex Queries Submissions")
                st.dataframe(lesson_df, use_container_width=True)

                st.download_button("⬇️ Download all submissions", df.to_csv(index=False).encode("utf-8"), "submissions.csv")
            except Exception as e:
                st.error(f"⚠️ Error reading CSV: {e}")
        else:
            st.info("No submissions yet.")
    elif password:
        st.error("Incorrect password.")
