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
Explore **Aggregations**, **JOINs**, and **Subqueries** step-by-step with multiple practice tasks.
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
    # Sample data
    cursor.executemany("INSERT INTO departments (name, manager) VALUES (?, ?)", [
        ("IT", "Peter Nagy"), ("HR", "Anna Kovacs"), ("Marketing", "Eszter Toth"),
        ("Finance", "Gabor Kiss"), ("Sales", "Marta Novak")
    ])
    cursor.executemany("INSERT INTO employees (name, department_id, salary, hire_date) VALUES (?, ?, ?, ?)", [
        ("Adam Kiss", 1, 800000, "2020-01-10"),
        ("Julia Farkas", 2, 500000, "2021-06-03"),
        ("Robert Toth", 3, 450000, "2019-11-17"),
        ("Eva Horvath", 1, 750000, "2022-02-12"),
        ("Lajos Szabo", 4, 600000, "2018-09-01"),
        ("Marta Nagy", 5, 700000, "2019-04-21")
    ])
    cursor.executemany("INSERT INTO projects (name, budget, department_id) VALUES (?, ?, ?)", [
        ("Website Redesign", 1200000, 1),
        ("Recruitment Drive", 400000, 2),
        ("Ad Campaign", 900000, 3),
        ("ERP Upgrade", 2000000, 4),
        ("Sales Blitz", 750000, 5)
    ])
    cursor.executemany("INSERT INTO tasks (project_id, assigned_to, hours, status) VALUES (?, ?, ?, ?)", [
        (1, 1, 50, "Done"), (1, 1, 30, "In Progress"),
        (2, 2, 25, "Done"), (3, 3, 40, "In Progress"),
        (4, 4, 100, "Done"), (5, 6, 80, "Done")
    ])
    conn.commit()

    # --- TASK LISTS (Aggregations first) ---
    task_types = {
        "Aggregations": [
            {
                "story": "🗓️ The HR system tracks hiring dates — you need to verify them.",
                "tip": "You can rename columns using AS for clarity.",
                "task": "Show each employee’s name and hire_date as 'Started On'.",
                "expected": "SELECT name, hire_date AS 'Started On' FROM employees;"
            },
            {
                "story": "💰 Finance wants total salary per department.",
                "tip": "Use SUM() and GROUP BY.",
                "task": "Show department_id and total salary.",
                "expected": "SELECT department_id, SUM(salary) AS total_salary FROM employees GROUP BY department_id;"
            },
            {
                "story": "📊 Average salary per department over 500k.",
                "tip": "Use HAVING to filter aggregated results.",
                "task": "Show department_id and average salary where AVG(salary) > 500000.",
                "expected": "SELECT department_id, AVG(salary) AS avg_salary FROM employees GROUP BY department_id HAVING AVG(salary) > 500000;"
            },
            {
                "story": "🧮 Count employees per department.",
                "tip": "COUNT(*) counts rows per group.",
                "task": "Show department_id and number of employees.",
                "expected": "SELECT department_id, COUNT(*) AS employee_count FROM employees GROUP BY department_id;"
            },
            {
                "story": "📈 Departments with more than 1 employee and avg salary > 500k.",
                "tip": "Combine COUNT(*) and AVG() with HAVING.",
                "task": "Show department_id, employee count and avg salary.",
                "expected": "SELECT department_id, COUNT(*) AS emp_count, AVG(salary) AS avg_salary FROM employees GROUP BY department_id HAVING COUNT(*) > 1 AND AVG(salary) > 500000;"
            },
            {
                "story": "💹 Max and min salary per department.",
                "tip": "Use MAX() and MIN() functions.",
                "task": "Show department_id, max salary, min salary.",
                "expected": "SELECT department_id, MAX(salary) AS max_salary, MIN(salary) AS min_salary FROM employees GROUP BY department_id;"
            },
            {
                "story": "🔢 Total hours worked per employee.",
                "tip": "Join tasks with employees first.",
                "task": "Show employee name and total hours.",
                "expected": "SELECT e.name, SUM(t.hours) AS total_hours FROM employees e JOIN tasks t ON e.id = t.assigned_to GROUP BY e.name;"
            },
            {
                "story": "📊 Average task hours per project.",
                "tip": "Group by project_id.",
                "task": "Show project_id and average hours.",
                "expected": "SELECT project_id, AVG(hours) AS avg_hours FROM tasks GROUP BY project_id;"
            },
            {
                "story": "📈 Projects with more than 1 employee assigned.",
                "tip": "COUNT(DISTINCT assigned_to) counts unique employees per project.",
                "task": "Show project_id and number of employees assigned > 1.",
                "expected": "SELECT project_id, COUNT(DISTINCT assigned_to) AS emp_count FROM tasks GROUP BY project_id HAVING COUNT(DISTINCT assigned_to) > 1;"
            },
            {
                "story": "💼 Sum of budget per department where total budget > 1,000,000.",
                "tip": "Use HAVING to filter sum of budgets.",
                "task": "Show department_id and total budget.",
                "expected": "SELECT department_id, SUM(budget) AS total_budget FROM projects GROUP BY department_id HAVING SUM(budget) > 1000000;"
            },
            {
                "story": "📊 Count tasks per status.",
                "tip": "GROUP BY status to see Done/In Progress count.",
                "task": "Show task status and count.",
                "expected": "SELECT status, COUNT(*) AS status_count FROM tasks GROUP BY status;"
            },
            {
                "story": "📈 Departments with max salary > 700,000.",
                "tip": "Use MAX() with HAVING.",
                "task": "Show department_id and max salary.",
                "expected": "SELECT department_id, MAX(salary) AS max_salary FROM employees GROUP BY department_id HAVING MAX(salary) > 700000;"
            }
        ],

        "JOINs": [
            {
                "story": "📚 JOIN Types Overview — quick summary.",
                "tip": "INNER JOIN: only matching rows. LEFT JOIN: all left rows. RIGHT JOIN: all right rows. FULL JOIN: all rows both sides.",
                "task": "Read the summary and understand the join types. No query needed.",
                "expected": "SELECT 'INNER, LEFT, RIGHT, FULL' AS join_types;"
            },
            {
                "story": "💼 Show project names with department managers.",
                "tip": "Use INNER JOIN on department_id.",
                "task": "Show project name and manager.",
                "expected": "SELECT p.name AS project, d.manager FROM projects p JOIN departments d ON p.department_id = d.id;"
            },
            {
                "story": "🏢 List all departments and their projects (even if no project).",
                "tip": "Use LEFT JOIN.",
                "task": "Show department name and project name.",
                "expected": "SELECT d.name AS department, p.name AS project FROM departments d LEFT JOIN projects p ON d.id = p.department_id;"
            },
            {
                "story": "📌 List all projects with their department name (even if department missing).",
                "tip": "Simulate RIGHT JOIN using LEFT JOIN by swapping tables.",
                "task": "Show project name and department name.",
                "expected": "SELECT p.name AS project, d.name AS department FROM departments d LEFT JOIN projects p ON d.id = p.department_id;"
            },
            {
                "story": "🌐 Full outer join simulation — all departments and projects.",
                "tip": "Use LEFT JOIN + UNION to simulate FULL OUTER JOIN.",
                "task": "Show department name and project name.",
                "expected": """
                SELECT d.name AS department, p.name AS project
                FROM departments d LEFT JOIN projects p ON d.id = p.department_id
                UNION
                SELECT d.name AS department, p.name AS project
                FROM departments d RIGHT JOIN projects p ON d.id = p.department_id;
                """
            },
            {
                "story": "🧩 Employees and their tasks (even if no tasks assigned).",
                "tip": "Use LEFT JOIN on tasks.",
                "task": "Show employee name and task status.",
                "expected": "SELECT e.name AS employee, t.status FROM employees e LEFT JOIN tasks t ON e.id = t.assigned_to;"
            },
            {
                "story": "📌 Show projects and number of tasks per project.",
                "tip": "Join tasks and projects and use COUNT() and GROUP BY.",
                "task": "Show project name and task count.",
                "expected": "SELECT p.name, COUNT(t.id) AS task_count FROM projects p LEFT JOIN tasks t ON p.id = t.project_id GROUP BY p.name;"
            },
            {
                "story": "💼 Employees with department name and number of tasks assigned.",
                "tip": "Use LEFT JOIN for tasks and INNER JOIN for department.",
                "task": "Show employee, department, task count.",
                "expected": "SELECT e.name, d.name AS department, COUNT(t.id) AS task_count FROM employees e JOIN departments d ON e.department_id = d.id LEFT JOIN tasks t ON e.id = t.assigned_to GROUP BY e.name, d.name;"
            },
            {
                "story": "📊 List all tasks and the employee name (even if not assigned).",
                "tip": "Use LEFT JOIN on employees.",
                "task": "Show task id and employee name.",
                "expected": "SELECT t.id, e.name AS employee FROM tasks t LEFT JOIN employees e ON t.assigned_to = e.id;"
            },
            {
                "story": "💻 Departments with total project budget and total hours of tasks.",
                "tip": "Join projects and tasks and aggregate per department.",
                "task": "Show department_id, total_budget, total_hours.",
                "expected": """
                SELECT d.id AS department_id, SUM(p.budget) AS total_budget, SUM(t.hours) AS total_hours
                FROM departments d
                LEFT JOIN projects p ON d.id = p.department_id
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY d.id;
                """
            },
            {
                "story": "📈 Employees with avg task hours and department.",
                "tip": "Use JOIN and AVG() aggregation.",
                "task": "Show employee name, avg hours, department name.",
                "expected": """
                SELECT e.name, AVG(t.hours) AS avg_hours, d.name AS department
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                LEFT JOIN tasks t ON e.id = t.assigned_to
                GROUP BY e.name, d.name;
                """
            },
            {
                "story": "💡 Final challenge — choose the correct JOINs yourself.",
                "tip": "No hint: decide which JOIN type fits.",
                "task": "List all projects, their department, and number of employees assigned to tasks (0 if none).",
                "expected": """
                SELECT p.name AS project, d.name AS department, COUNT(t.assigned_to) AS emp_count
                FROM projects p
                LEFT JOIN departments d ON p.department_id = d.id
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY p.name, d.name;
                """
            }
        ],
        "Subqueries": [
            {
                "story": "🌀 List employees in departments with high-budget projects.",
                "tip": "Use WHERE ... IN (subquery).",
                "task": "Show employee names in departments where any project budget > 1,000,000.",
                "expected": "SELECT name FROM employees WHERE department_id IN (SELECT department_id FROM projects WHERE budget > 1000000);"
            },
            {
                "story": "🧮 Count projects per department using subquery in SELECT.",
                "tip": "Use (SELECT COUNT(*) ...) AS alias.",
                "task": "Show department name and project count.",
                "expected": "SELECT d.name, (SELECT COUNT(*) FROM projects p WHERE p.department_id = d.id) AS project_count FROM departments d;"
            },
            {
                "story": "📌 Find employees with salary above department average.",
                "tip": "Use subquery in WHERE for comparison.",
                "task": "Show employee name and salary if salary > department average.",
                "expected": "SELECT name, salary FROM employees e WHERE salary > (SELECT AVG(salary) FROM employees WHERE department_id = e.department_id);"
            },
            {
                "story": "📊 Projects with more tasks than average per project.",
                "tip": "Use COUNT(*) in subquery to compare.",
                "task": "Show project name and task count > average task count.",
                "expected": "SELECT name FROM projects p WHERE (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) > (SELECT AVG(task_count) FROM (SELECT COUNT(*) AS task_count FROM tasks GROUP BY project_id));"
            },
            {
                "story": "💼 Employees in departments with min salary < 500,000.",
                "tip": "Use subquery in WHERE with MIN().",
                "task": "Show employee name and department_id.",
                "expected": "SELECT name, department_id FROM employees WHERE department_id IN (SELECT department_id FROM employees GROUP BY department_id HAVING MIN(salary) < 500000);"
            },
            {
                "story": "🔢 Departments with more than one high-earning employee.",
                "tip": "Combine COUNT(*) in HAVING with subquery.",
                "task": "Show department_id with count > 1 for salary > 600,000.",
                "expected": "SELECT department_id FROM employees GROUP BY department_id HAVING COUNT(CASE WHEN salary > 600000 THEN 1 END) > 1;"
            },
            {
                "story": "🧮 Employees who have done tasks with more than 40 hours.",
                "tip": "Use EXISTS or IN with tasks table.",
                "task": "Show employee names who have tasks with hours > 40.",
                "expected": "SELECT name FROM employees e WHERE EXISTS (SELECT 1 FROM tasks t WHERE t.assigned_to = e.id AND t.hours > 40);"
            },
            {
                "story": "📈 Departments with max project budget over 1,000,000.",
                "tip": "Use subquery with MAX() in WHERE.",
                "task": "Show department name and max budget > 1,000,000.",
                "expected": "SELECT name FROM departments WHERE id IN (SELECT department_id FROM projects GROUP BY department_id HAVING MAX(budget) > 1000000);"
            },
            {
                "story": "💡 Employees assigned to all tasks of a specific project.",
                "tip": "Use subquery to ensure employee appears in all tasks.",
                "task": "Show employee names assigned to all tasks in project_id = 1.",
                "expected": "SELECT name FROM employees e WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.project_id = 1 AND t.assigned_to <> e.id);"
            },
            {
                "story": "📊 Projects where total task hours exceed 70.",
                "tip": "Use subquery with SUM() in WHERE.",
                "task": "Show project names with total hours > 70.",
                "expected": "SELECT name FROM projects p WHERE (SELECT SUM(hours) FROM tasks t WHERE t.project_id = p.id) > 70;"
            },
            {
                "story": "📝 Employees whose salary is above the overall average.",
                "tip": "Use scalar subquery with AVG() in WHERE.",
                "task": "Show employee name and salary.",
                "expected": "SELECT name, salary FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);"
            },
            {
                "story": "💻 Final challenge — flexible subquery.",
                "tip": "Decide whether to use IN, EXISTS or scalar subquery.",
                "task": "Show departments where employees have done more than 30 hours on tasks.",
                "expected": "SELECT DISTINCT department_id FROM employees e WHERE EXISTS (SELECT 1 FROM tasks t WHERE t.assigned_to = e.id AND t.hours > 30);"
            }
        ]
    }

    # --- Task Navigation ---
    task_type = st.sidebar.selectbox("Choose Task Type", list(task_types.keys()))
    if "task_index" not in st.session_state:
        st.session_state.task_index = 0

    tasks = task_types[task_type]
    task = tasks[st.session_state.task_index]

    st.subheader(f"{task_type} – Task {st.session_state.task_index+1}")
    st.info(task["story"])
    st.caption(f"Tip: {task['tip']}")
    if "visual" in task:
        st.markdown(f"Visualization: {task['visual']}")
    st.write(task["task"])

    sql_query = st.text_area("✍️ Write your SQL query:")

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

    def log_submission(name, query, correct, score, task_type, task_index):
        file_exists = os.path.isfile("submissions.csv")
        with open("submissions.csv","a",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp","name","category","task_index","query","correct","score"])
            writer.writerow([datetime.now().isoformat(),name,task_type,task_index,query,correct,score])

    if st.button("▶️ Run Query"):
        try:
            df = pd.read_sql_query(sql_query, conn)
            st.success("✅ Query executed successfully!")
            st.dataframe(df,use_container_width=True)
            expected_df = pd.read_sql_query(task["expected"],conn)
            # Flexible comparison: sort columns and rows
            df_sorted = df.sort_index(axis=1).sort_values(by=list(df.columns)).reset_index(drop=True)
            expected_sorted = expected_df.sort_index(axis=1).sort_values(by=list(expected_df.columns)).reset_index(drop=True)
            if df_sorted.equals(expected_sorted):
                st.success(f"🎉 Correct answer, {name}!")
                correct = True
                score = 1
            else:
                st.warning("❌ Not quite right — check your logic.")
                correct = False
                score = 0
            log_submission(name,sql_query,correct,score,task_type,st.session_state.task_index)
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
                st.dataframe(df,use_container_width=True)
                st.download_button("⬇️ Download all submissions", df.to_csv(index=False).encode("utf-8"), "submissions.csv")
            except Exception as e:
                st.error(f"⚠️ Error reading CSV: {e}")
        else:
            st.info("No submissions yet.")
    elif password:
        st.error("Incorrect password.")
