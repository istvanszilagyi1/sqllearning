import streamlit as st
import sqlite3
import pandas as pd
import csv
from datetime import datetime
import os
import graphviz

TEACHER_PASSWORD = "sql2025"

st.set_page_config(page_title="SQL Training App", layout="wide")

st.title("🎓 Interactive SQL Training App xddddd")
st.write("Students: Enter your name, select a task type, complete the SQL task, and run your query. Results are logged automatically.")

if "score" not in st.session_state:
    st.session_state.score = 0
if "name" not in st.session_state:
    st.session_state.name = ""
if "task_index" not in st.session_state:
    st.session_state.task_index = 0

def reset_task_index():
    st.session_state.task_index = 0

def toggle_er_diagram():
    """Toggles the visibility state of the ER Diagram."""
    st.session_state.show_er_diagram = not st.session_state.show_er_diagram

def create_er_diagram():
    """Generates the Graphviz diagram with improved styling and record shapes."""
    dot = graphviz.Digraph(
        comment='Database Schema',
        # Graph styling
        graph_attr={'rankdir': 'LR', 'bgcolor': '#f0f2f6', 'fontname': 'Inter', 'splines': 'ortho'},
        # Node styling
        node_attr={'shape': 'record', 'style': 'filled', 'fillcolor': '#ffffff', 'fontname': 'Inter', 'color': '#1f77b4'},
        # Edge styling
        edge_attr={'fontname': 'Inter', 'color': '#555555', 'arrowhead': 'crow'}
    )

    # Nodes (Tables) using the 'record' shape for detailed structure
    dot.node('employees', '{employees | id PK | name | department_id FK | salary | hire_date}')
    dot.node('departments', '{departments | id PK | name | manager}')
    dot.node('sales', '{sales | id PK | employee_id FK | product | amount | sale_date}')
    dot.node('customers', '{customers | id PK | name | country | industry}')

    # Edges (Relationships)
    # Departments (1) -> Employees (N)
    dot.edge('departments', 'employees', label='1:N (department_id)')
    # Employees (1) -> Sales (N)
    dot.edge('employees', 'sales', label='1:N (employee_id)')

    return dot

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

    # --- Sidebar: Detailed schema + ER Diagram ---

    task_type = st.sidebar.selectbox("Select task type:", ["SELECT basics", "WHERE filters", "ORDER BY", "GROUP BY"], key="task_type_selector", on_change=reset_task_index)

    st.sidebar.header("Database Schema & Examples")
    
    st.sidebar.button(
        f"{'Hide' if st.session_state.show_er_diagram else 'Show'} ER Diagram", 
        on_click=toggle_er_diagram
    )


    st.sidebar.markdown("""
    **employees**  
    - id: integer, PK  
    - name: text (e.g., 'Anna Kovacs')  
    - department_id: integer (FK to departments)  
    - salary: integer (e.g., 400000)  
    - hire_date: date ('YYYY-MM-DD')  

    **departments**  
    - id: integer, PK  
    - name: text (e.g., 'IT')  
    - manager: text (e.g., 'Peter Nagy')  

    **sales**  
    - id: integer, PK  
    - employee_id: integer (FK to employees)  
    - product: text  
    - amount: integer  
    - sale_date: date  

    **customers**  
    - id: integer, PK  
    - name: text  
    - country: text  
    - industry: text  
    """)

    # --- Tasks dictionary ---
    tasks = {
        "SELECT basics": [
            {"story": "🕵️‍♀️ You are the new HR detective. Peek at all employees' names, departments, and salaries.",
             "tip": "Use SELECT to choose which columns to view.",
             "task": "List all employees with their name, department_id, and salary.",
             "expected": "SELECT * FROM employees;"}
        ],
        "WHERE filters": [
            {"story": "💼 The IT manager is curious who's earning more than 600,000 HUF.",
             "tip": "Use WHERE to filter rows by a condition.",
             "task": "List all IT employees with salary greater than 600,000.",
             "expected": "SELECT * FROM employees WHERE department_id=2 AND salary>600000;"}
        ],
        "ORDER BY": [
            {"story": "📅 HR wants to send welcome emails to the newest recruits.",
             "tip": "Use ORDER BY to sort results ascending or descending.",
             "task": "List all employees ordered by hire_date descending.",
             "expected": "SELECT * FROM employees ORDER BY hire_date DESC;"}
        ],
        "GROUP BY": [
            {"story": "🏢 The CEO is counting how many employees are in each department.",
             "tip": "Use GROUP BY to group rows and COUNT() to count them.",
             "task": "Count the number of employees per department.",
             "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id;"}
        ]
    }

    # --- Show current task ---
    tasks_list = tasks.get(task_type, [])
    safe_index = min(st.session_state.task_index, len(tasks_list) - 1)
    current_task = tasks_list[safe_index]

    st.subheader(f"🧠 {task_type} Task")
    st.markdown(f"**Story:** {current_task['story']}")
    st.markdown(f"**SQL Tip:** {current_task['tip']}")
    st.markdown(f"**Task:** {current_task['task']}")

    sql_query = st.text_area("Write your SQL query here:", height=150)

    # --- Run Query button ---
    if st.button("Run Query"):
        try:
            df = pd.read_sql_query(sql_query, conn)
            st.success("✅ Query executed successfully!")
            st.dataframe(df, use_container_width=True)

            numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
            if len(numeric_cols) > 0:
                st.subheader("📊 Visualization")
                st.bar_chart(df[numeric_cols])

            expected_df = pd.read_sql_query(current_task["expected"], conn)
            correct = df.equals(expected_df)
            if correct:
                st.success(f"🎉 Correct answer, {st.session_state.name}! +1 point")
                st.session_state.score += 1
            else:
                st.info("❌ Not the expected result. Try again!")

            file_exists = os.path.isfile("submissions.csv")
            with open("submissions.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if not file_exists:
                    writer.writerow(["timestamp", "name", "task_type", "task_index", "query", "correct", "score"])
                writer.writerow(
                    [datetime.now().isoformat(), st.session_state.name, task_type, st.session_state.task_index,
                     sql_query, correct, st.session_state.score])

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

    # --- Next task button ---
    if st.button("Next Task"):
        if st.session_state.task_index < len(tasks[task_type]) - 1:
            st.session_state.task_index += 1
        else:
            st.info("No more tasks in this type. You can choose another type.")

    st.divider()
    st.subheader(f"🏅 Current Score for {st.session_state.name}: {st.session_state.score}")

# ==================== TEACHER MODE ====================
else:
    st.subheader("🔐 Teacher Dashboard")
    password = st.text_input("Enter teacher password:", type="password")

    if password == TEACHER_PASSWORD:
        st.success("Access granted. Welcome, teacher!")

        # --- Check if CSV exists ---
        if os.path.exists("submissions.csv"):
            try:
                df = pd.read_csv("submissions.csv", encoding="utf-8", on_bad_lines="skip")
                st.dataframe(df, use_container_width=True)
                st.download_button(
                    "⬇️ Download submissions (CSV)",
                    df.to_csv(index=False).encode("utf-8"),
                    file_name="submissions.csv"
                )
            except Exception as e:
                st.error(f"⚠️ Error reading submissions.csv: {e}")

    elif password:
        st.error("Incorrect password.")
