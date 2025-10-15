import streamlit as st
import sqlite3
import pandas as pd
import csv
from datetime import datetime
import os
import graphviz

TEACHER_PASSWORD = "sql2025"

st.set_page_config(page_title="SQL Training App", layout="wide")

st.title("🎓 Interactive SQL Training App")
st.write("Students: Enter your name, select a task type, complete the SQL task, and run your query. Results are logged automatically.")

st.session_state.setdefault("score", 0)
st.session_state.setdefault("name", "")
st.session_state.setdefault("task_index", 0)
st.session_state.setdefault("show_er_diagram", False)

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

    task_type = st.sidebar.selectbox("Select task type:", ["SELECT basics", "WHERE filters", "ORDER BY", "GROUP BY", "HAVING"], key="task_type_selector", on_change=reset_task_index)

    st.sidebar.header("Database Schema & Examples")
    
    st.sidebar.button(
        f"{'Hide' if st.session_state.show_er_diagram else 'Show'} ER Diagram", 
        on_click=toggle_er_diagram
    )

    if st.session_state.show_er_diagram:
        st.subheader("📊 Database ER Diagram")
        st.graphviz_chart(create_er_diagram(), use_container_width=True)
        st.divider()


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
            {
                "story": "🧑‍💻 You just started your internship at a software company. Your manager asks you to check the employee records in the system.",
                "tip": "Use SELECT to view all columns from a table.",
                "task": "List all columns from the employees table.",
                "expected": "SELECT * FROM employees;"
            },
            {
                "story": "📋 The HR team wants to review only employee names and salaries.",
                "tip": "You can specify which columns to select.",
                "task": "List the name and salary of every employee.",
                "expected": "SELECT name, salary FROM employees;"
            },
            {
                "story": "🏢 You’re preparing a summary for department managers.",
                "tip": "Combine information from two tables using JOIN.",
                "task": "List each employee’s name with their department’s name.",
                "expected": "SELECT e.name, d.name AS department FROM employees e JOIN departments d ON e.department_id = d.id;"
            },
            {
                "story": "💰 The finance intern wants to know everyone’s salary and hire date.",
                "tip": "Use SELECT with multiple columns.",
                "task": "Show all employees’ names, salaries, and hire dates.",
                "expected": "SELECT name, salary, hire_date FROM employees;"
            },
            {
                "story": "🧾 Your supervisor wants to double-check the list of all departments.",
                "tip": "SELECT can also be used on small tables like departments.",
                "task": "Display all departments with their manager names.",
                "expected": "SELECT name, manager FROM departments;"
            },
            {
                "story": "📦 The sales department needs a list of all products that were sold.",
                "tip": "Use DISTINCT to avoid duplicates.",
                "task": "Show the unique product names from the sales table.",
                "expected": "SELECT DISTINCT product FROM sales;"
            },
            {
                "story": "🗓️ The HR system tracks hiring dates — you need to verify them.",
                "tip": "You can rename columns using AS for clarity.",
                "task": "Show each employee’s name and hire_date as 'Started On'.",
                "expected": "SELECT name, hire_date AS 'Started On' FROM employees;"
            },
            {
                "story": "🧠 Your team lead wants to see how the tables are related.",
                "tip": "Try a simple JOIN to combine employees and departments.",
                "task": "List employee names along with their manager names from departments.",
                "expected": "SELECT e.name, d.manager FROM employees e JOIN departments d ON e.department_id = d.id;"
            },
        ],

        "WHERE filters": [
            {
                "story": "💼 Your manager asks: who earns more than 600,000 HUF?",
                "tip": "Use WHERE with a numeric comparison.",
                "task": "List employees whose salary is above 600,000.",
                "expected": "SELECT * FROM employees WHERE salary > 600000;"
            },
            {
                "story": "🧑‍💼 The IT manager only wants to see IT department employees.",
                "tip": "Filter results by department_id or name.",
                "task": "List all employees from the IT department.",
                "expected": "SELECT * FROM employees WHERE department_id = 2;"
            },
            {
                "story": "📆 HR wants to see employees hired after 2020.",
                "tip": "Use WHERE with a date condition.",
                "task": "Show employees whose hire_date is after 2020-12-31.",
                "expected": "SELECT * FROM employees WHERE hire_date > '2020-12-31';"
            },
            {
                "story": "🎯 The marketing team wants to review salaries below 500,000.",
                "tip": "Combine comparisons using WHERE.",
                "task": "List employees with salaries less than 500,000.",
                "expected": "SELECT * FROM employees WHERE salary < 500000;"
            },
            {
                "story": "🌍 The sales intern wants to focus on Hungarian customers.",
                "tip": "Use a WHERE condition on text columns.",
                "task": "List all customers from Hungary.",
                "expected": "SELECT * FROM customers WHERE country = 'Hungary';"
            },
            {
                "story": "🕵️ You’re auditing data and need to find employees named 'Anna Kovacs'.",
                "tip": "Filter text values exactly.",
                "task": "Find the row of employee Anna Kovacs.",
                "expected": "SELECT * FROM employees WHERE name = 'Anna Kovacs';"
            },
            {
                "story": "💸 Your manager suspects some salaries are between 400,000 and 600,000.",
                "tip": "Use BETWEEN for range checks.",
                "task": "List employees with salaries between 400,000 and 600,000.",
                "expected": "SELECT * FROM employees WHERE salary BETWEEN 400000 AND 600000;"
            },
            {
                "story": "📧 HR wants to find all employees not in the HR department.",
                "tip": "Use the NOT operator.",
                "task": "List employees who are not in department 1 (HR).",
                "expected": "SELECT * FROM employees WHERE department_id != 1;"
            },
        ],

        "ORDER BY": [
            {
                "story": "📅 The HR manager wants to see the newest employees first.",
                "tip": "Use ORDER BY with DESC for descending order.",
                "task": "List all employees ordered by hire_date descending.",
                "expected": "SELECT * FROM employees ORDER BY hire_date DESC;"
            },
            {
                "story": "💵 The finance team wants to review employees from the lowest to highest salary.",
                "tip": "Default ORDER BY sorts ascending.",
                "task": "List employees ordered by salary ascending.",
                "expected": "SELECT * FROM employees ORDER BY salary ASC;"
            },
            {
                "story": "🏷️ The IT director wants an alphabetical list of all departments.",
                "tip": "ORDER BY also works on text columns.",
                "task": "List all departments in alphabetical order.",
                "expected": "SELECT * FROM departments ORDER BY name ASC;"
            },
            {
                "story": "🧾 You’re making a sales dashboard showing the largest deals first.",
                "tip": "Use ORDER BY amount DESC.",
                "task": "List all sales ordered by amount descending.",
                "expected": "SELECT * FROM sales ORDER BY amount DESC;"
            },
            {
                "story": "📊 Marketing wants to see which sales happened most recently.",
                "tip": "Sort by sale_date descending.",
                "task": "Show all sales ordered by sale_date descending.",
                "expected": "SELECT * FROM sales ORDER BY sale_date DESC;"
            },
            {
                "story": "📈 The HR manager only needs the top 3 earners.",
                "tip": "Use ORDER BY with LIMIT.",
                "task": "List the 3 highest-paid employees.",
                "expected": "SELECT * FROM employees ORDER BY salary DESC LIMIT 3;"
            },
            {
                "story": "📉 The CEO wants to see the two lowest-paid employees.",
                "tip": "ORDER BY ascending, then LIMIT.",
                "task": "Show the 2 employees with the smallest salaries.",
                "expected": "SELECT * FROM employees ORDER BY salary ASC LIMIT 2;"
            },
            {
                "story": "🗂️ HR wants to review the five earliest hires.",
                "tip": "Order by hire_date ascending, limit the result.",
                "task": "List the first 5 employees hired.",
                "expected": "SELECT * FROM employees ORDER BY hire_date ASC LIMIT 5;"
            },
        ],

        "GROUP BY": [
            {
                "story": "🏢 The CEO wants to know how many employees work in each department.",
                "tip": "Use COUNT() with GROUP BY.",
                "task": "Count the number of employees per department.",
                "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id;"
            },
            {
                "story": "💸 The finance team wants to see the average salary per department.",
                "tip": "Use AVG() to calculate averages.",
                "task": "Show department_id and average salary for each department.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id;"
            },
            {
                "story": "🧾 Marketing wants to know total sales amounts per product.",
                "tip": "Use SUM() with GROUP BY.",
                "task": "List each product and the total sales amount.",
                "expected": "SELECT product, SUM(amount) FROM sales GROUP BY product;"
            },
            {
                "story": "🧍‍♀️ HR wants to count how many people were hired each year.",
                "tip": "Use strftime to extract the year from hire_date.",
                "task": "Count employees grouped by year of hire_date.",
                "expected": "SELECT strftime('%Y', hire_date) AS year, COUNT(*) FROM employees GROUP BY year;"
            },
            {
                "story": "💼 Management wants to see the total salary budget per department.",
                "tip": "Use SUM() with GROUP BY.",
                "task": "Show department_id and total salary per department.",
                "expected": "SELECT department_id, SUM(salary) FROM employees GROUP BY department_id;"
            },
            {
                "story": "📊 The IT team wants to check how many sales each employee made.",
                "tip": "Group by employee_id in the sales table.",
                "task": "Count sales per employee_id.",
                "expected": "SELECT employee_id, COUNT(*) FROM sales GROUP BY employee_id;"
            },
            {
                "story": "🪙 The CEO asks for the average deal size per employee.",
                "tip": "Use AVG(amount) grouped by employee_id.",
                "task": "Show employee_id and their average sale amount.",
                "expected": "SELECT employee_id, AVG(amount) FROM sales GROUP BY employee_id;"
            },
            {
                "story": "🏷️ The HR manager wants to know how many managers each department has listed.",
                "tip": "Use COUNT() grouped by manager name.",
                "task": "Count the number of departments for each manager.",
                "expected": "SELECT manager, COUNT(*) FROM departments GROUP BY manager;"
            },
        ],

        "HAVING": [
            {
                "story": "💰 The CEO wants to see departments where the average salary is over 500,000.",
                "tip": "Use HAVING to filter aggregated results.",
                "task": "Show department_id and average salary where AVG(salary) > 500,000.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id HAVING AVG(salary) > 500000;"
            },
            {
                "story": "📦 The sales director wants to see products that generated more than 15,000 total revenue.",
                "tip": "Use HAVING with SUM().",
                "task": "List product names where total sales exceed 15,000.",
                "expected": "SELECT product, SUM(amount) FROM sales GROUP BY product HAVING SUM(amount) > 15000;"
            },
            {
                "story": "🧾 HR wants departments that have more than one employee.",
                "tip": "HAVING works after GROUP BY.",
                "task": "Show department_id and COUNT(*) where more than one employee exists.",
                "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id HAVING COUNT(*) > 1;"
            },
            {
                "story": "📈 The CEO wants employees who have made more than one sale.",
                "tip": "Group by employee_id, then filter with HAVING COUNT() > 1.",
                "task": "List employee_id and number of sales where count > 1.",
                "expected": "SELECT employee_id, COUNT(*) FROM sales GROUP BY employee_id HAVING COUNT(*) > 1;"
            },
            {
                "story": "🗓️ Management wants to find hire years with more than one hire.",
                "tip": "Combine strftime and HAVING.",
                "task": "List years with more than one employee hired.",
                "expected": "SELECT strftime('%Y', hire_date) AS year, COUNT(*) FROM employees GROUP BY year HAVING COUNT(*) > 1;"
            },
            {
                "story": "💸 The finance team only wants to see departments whose total salary is at least 1,000,000.",
                "tip": "Use SUM() and HAVING together.",
                "task": "List department_id and total salary where total ≥ 1,000,000.",
                "expected": "SELECT department_id, SUM(salary) FROM employees GROUP BY department_id HAVING SUM(salary) >= 1000000;"
            },
            {
                "story": "🎯 The marketing team only cares about employees who have average sales above 12,000.",
                "tip": "Use AVG() in HAVING.",
                "task": "Show employee_id with average sale amount > 12,000.",
                "expected": "SELECT employee_id, AVG(amount) FROM sales GROUP BY employee_id HAVING AVG(amount) > 12000;"
            },
            {
                "story": "🏢 HR wants to find managers who manage more than one department.",
                "tip": "Use GROUP BY manager and HAVING COUNT()>1.",
                "task": "Show managers who manage multiple departments.",
                "expected": "SELECT manager, COUNT(*) FROM departments GROUP BY manager HAVING COUNT(*) > 1;"
            },
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
            st.session_state.sql_query_input = ""
            st.rerun()
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
