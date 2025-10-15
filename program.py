import streamlit as st
import time
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
    st.session_state.show_er_diagram = not st.session_state.show_er_diagram

def create_er_diagram():
    def create_table_label(name, fields):
        html_content = f'''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#ffffff" COLOR="#1f77b4" >
    <TR><TD COLSPAN="1" BGCOLOR="#1f77b4" ALIGN="LEFT"><FONT COLOR="#ffffff" POINT-SIZE="14"><B>{name}</B></FONT></TD></TR>'''

        for field in fields:
            formatted_field = field.replace('PK', '<B>PK</B>').replace('FK', '<B>FK</B>')
            html_content += f'''<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">{formatted_field}</FONT></TD></TR>'''
            
        html_content += '</TABLE>>'
        return html_content

    dot = graphviz.Digraph(
        comment='Database Schema',
        graph_attr={
            'rankdir': 'LR', 
            'bgcolor': '#f0f2f6', 
            'fontname': 'Inter', 
            'splines': 'ortho'
        },
        # Node styling
        node_attr={
            'shape': 'plaintext',
            'fontname': 'Inter'
        },
        edge_attr={
            'fontname': 'Inter', 
            'color': '#555555', 
            'arrowhead': 'crow',
            'arrowtail': 'none',
            'dir': 'forward'
        }
    )

    
    employees_fields = ['id PK', 'name', 'department_id FK', 'salary', 'hire_date']
    departments_fields = ['id PK', 'name', 'manager']
    sales_fields = ['id PK', 'employee_id FK', 'product', 'amount', 'sale_date']
    customers_fields = ['id PK', 'name', 'country', 'industry']
    
    dot.node('employees', label=create_table_label('employees', employees_fields))
    dot.node('departments', label=create_table_label('departments', departments_fields))
    dot.node('sales', label=create_table_label('sales', sales_fields))
    dot.node('customers', label=create_table_label('customers', customers_fields))

    
    dot.edge('departments', 'employees', label='1:N (department_id)', tailport='e', headport='w')
    
    dot.edge('employees', 'sales', label='1:N (employee_id)', tailport='e', headport='w')

    return dot

# --- Mode selection ---
mode = st.sidebar.radio("Mode", ["Learner", "Instructor"])

# ==================== STUDENT MODE ====================
if mode == "Learner":

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
                "tip": "To see all columns, use the wildcard character: **SELECT * FROM**.",
                "task": "List all columns from the **employees** table.",
                "expected": "SELECT * FROM employees;"
            },
            {
                "story": "📋 The HR team wants to review only employee names and salaries.",
                "tip": "List columns by name, separated by commas: **SELECT column1, column2 FROM table;**",
                "task": "List the **name** and **salary** of every employee.",
                "expected": "SELECT name, salary FROM employees;"
            },
            {
                "story": "🏢 You’re preparing a summary for department managers.",
                "tip": "Use **SELECT * FROM** to view the entire table structure and data.",
                "task": "List all columns from the **departments** table.",
                "expected": "SELECT * FROM departments;"
            },
            {
                "story": "💰 The finance intern wants to know everyone’s salary and hire date.",
                "tip": "Remember to separate all three column names with commas in the **SELECT** clause.",
                "task": "Show all employees’ **name**, **salary**, and **hire_date**.",
                "expected": "SELECT name, salary, hire_date FROM employees;"
            },
            {
                "story": "🧾 Your supervisor wants to double-check the list of all departments.",
                "tip": "Specify the two required columns, **name** and **manager**, in the **SELECT** clause.",
                "task": "Display all department **name** and their **manager**.",
                "expected": "SELECT name, manager FROM departments;"
            },
            {
                "story": "📦 The sales department needs a list of all products that were sold.",
                "tip": "Use the **DISTINCT** keyword right after **SELECT** to return only unique values.",
                "task": "Show the unique **product** names from the **sales** table.",
                "expected": "SELECT DISTINCT product FROM sales;"
            },
            {
                "story": "🗓️ The HR system tracks hiring dates — you need to verify them.",
                "tip": "Use the **AS** keyword to rename a column: **SELECT column AS 'New Name'**.",
                "task": "Show each employee’s **name** and **hire_date** as 'Started On'.",
                "expected": "SELECT name, hire_date AS 'Started On' FROM employees;"
            },
            {
                "story": "🕵️ The CEO wants a quick list of all employee IDs to cross-reference with another system.",
                "tip": "Simply select the specific **id** column: **SELECT id FROM employees;**",
                "task": "Show all employee **id** values.",
                "expected": "SELECT id FROM employees;"
            }
        ],
        "WHERE filters": [
            {
                "story": "💼 Your manager asks: who earns more than 600,000 HUF?",
                "tip": "Use the **WHERE** clause with the greater-than operator: **salary > 600000**.",
                "task": "List all columns for employees whose **salary > 600000**.",
                "expected": "SELECT * FROM employees WHERE salary > 600000;"
            },
            {
                "story": "🧑‍💼 The IT manager only wants to see IT department employees.",
                "tip": "Filter results using the equality operator in the **WHERE** clause: **department_id = 2**.",
                "task": "List all columns for employees from **department_id = 2**.",
                "expected": "SELECT * FROM employees WHERE department_id = 2;"
            },
            {
                "story": "📆 HR wants to see employees hired before 2022.",
                "tip": "Use the less-than operator on a date string: **WHERE hire_date < '2022-01-01'**.",
                "task": "Show all columns for employees whose **hire_date < '2022-01-01'**.",
                "expected": "SELECT * FROM employees WHERE hire_date < '2022-01-01';"
            },
            {
                "story": "🎯 The marketing team wants to review sales where the amount was exactly 10,000.",
                "tip": "The basic form of a filter is: **WHERE column = value**.",
                "task": "List all columns for sales where **amount = 10000**.",
                "expected": "SELECT * FROM sales WHERE amount = 10000;"
            },
            {
                "story": "🌍 The sales intern wants to focus on customers *not* from France.",
                "tip": "Use the NOT EQUAL operator: **!=** or **<>**. Remember string values need single quotes.",
                "task": "List the customer **name** and **country** from the **customers** table where **country != 'France'**.",
                "expected": "SELECT name, country FROM customers WHERE country != 'France';"
            },
            {
                "story": "🕵️ The department head is looking for department 3, which is the 'Marketing' department.",
                "tip": "Filter the departments table using the **id** column with the equality operator.",
                "task": "Find the **name** and **manager** of the department where **id = 3**.",
                "expected": "SELECT name, manager FROM departments WHERE id = 3;"
            },
            {
                "story": "💸 Your manager suspects some sales are between 5,000 and 20,000.",
                "tip": "Use the **BETWEEN** keyword: **WHERE column BETWEEN value1 AND value2**.",
                "task": "List all columns for sales with **amount BETWEEN 5000 AND 20000**.",
                "expected": "SELECT * FROM sales WHERE amount BETWEEN 5000 AND 20000;"
            },
            {
                "story": "📧 HR needs to see employees who earn exactly 550,000.",
                "tip": "Use the equality operator (=) to select based on the **salary** value.",
                "task": "List the **name**, **salary**, and **department_id** for employees where **salary = 550000**.",
                "expected": "SELECT name, salary, department_id FROM employees WHERE salary = 550000;"
            }
        ],
        "ORDER BY": [
            {
                "story": "📅 The HR manager wants to see the newest employees first.",
                "tip": "Use the **ORDER BY** clause followed by **DESC** to sort from highest/latest to lowest/oldest.",
                "task": "List the employee **name** and **hire_date** ordered by **hire_date** descending.",
                "expected": "SELECT name, hire_date FROM employees ORDER BY hire_date DESC;"
            },
            {
                "story": "💵 The finance team wants to review employees from the lowest to highest salary.",
                "tip": "Use **ORDER BY** with **ASC** (or omit it, as ASC is the default) to sort from lowest to highest.",
                "task": "List all columns for employees ordered by **salary** ascending.",
                "expected": "SELECT * FROM employees ORDER BY salary ASC;"
            },
            {
                "story": "🏷️ The IT director wants a list of departments by their ID number, largest first.",
                "tip": "Sort by the **id** column and use **DESC**.",
                "task": "List all columns for departments ordered by **id** descending.",
                "expected": "SELECT * FROM departments ORDER BY id DESC;"
            },
            {
                "story": "🧾 You’re making a sales dashboard showing the smallest deals first.",
                "tip": "Use **ORDER BY amount ASC**.",
                "task": "List the **sale_date** and **amount** for sales ordered by **amount** ascending.",
                "expected": "SELECT sale_date, amount FROM sales ORDER BY amount ASC;"
            },
            {
                "story": "📊 Marketing wants to see which sales were registered by the lowest employee_id first.",
                "tip": "The required syntax is: **ORDER BY employee_id ASC**.",
                "task": "Show all columns for sales ordered by **employee_id** ascending.",
                "expected": "SELECT * FROM sales ORDER BY employee_id ASC;"
            },
            {
                "story": "📈 The HR manager only needs the top 3 earners.",
                "tip": "Combine **ORDER BY ... DESC** with the **LIMIT** clause to restrict the output rows: **LIMIT 3**.",
                "task": "List the **name** and **salary** for the **3 highest-paid** employees (ordered by salary DESC).",
                "expected": "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 3;"
            },
            {
                "story": "📉 The CEO wants to see the two department managers who are listed last alphabetically.",
                "tip": "Sort the **manager** column **DESC** to get Z-A, then use **LIMIT 2**.",
                "task": "Show the department **name** and **manager** for the **2 departments** whose **manager** name is alphabetically **last**.",
                "expected": "SELECT name, manager FROM departments ORDER BY manager DESC LIMIT 2;"
            },
            {
                "story": "🗂️ The sales team wants to see a list of their products from Z to A.",
                "tip": "Sort the **product** column using **DESC**.",
                "task": "List the **product** and **sale_date** for sales ordered by **product** descending.",
                "expected": "SELECT product, sale_date FROM sales ORDER BY product DESC;"
            }
        ],
        "GROUP BY": [
            {
                "story": "🏢 The CEO wants to know how many employees work in each department.",
                "tip": "Use **COUNT(*)** with **GROUP BY department_id**.",
                "task": "Show **department_id** and the **COUNT(\*)** of employees per department.",
                "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id;"
            },
            {
                "story": "💸 The finance team wants to see the average salary per department.",
                "tip": "Use the **AVG()** aggregate function and **GROUP BY** the department ID.",
                "task": "Show **department_id** and **AVG(salary)** for each department.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id;"
            },
            {
                "story": "🧾 Marketing wants to know total sales amounts per product.",
                "tip": "Use **SUM(amount)** to total the sales, and **GROUP BY product**.",
                "task": "List each **product** and the **SUM(amount)** of its sales.",
                "expected": "SELECT product, SUM(amount) FROM sales GROUP BY product;"
            },
            {
                "story": "💼 Management wants to see the total salary budget per department.",
                "tip": "The required aggregate function is **SUM(salary)**, which needs to be grouped by **department_id**.",
                "task": "Show **department_id** and **SUM(salary)** (total salary) per department.",
                "expected": "SELECT department_id, SUM(salary) FROM employees GROUP BY department_id;"
            },
            {
                "story": "📊 The IT team wants to check how many sales each employee made.",
                "tip": "Use **COUNT(\*)** and **GROUP BY employee_id** in the sales table.",
                "task": "Show **employee_id** and the **COUNT(\*)** of sales per employee.",
                "expected": "SELECT employee_id, COUNT(*) FROM sales GROUP BY employee_id;"
            },
            {
                "story": "🪙 The CEO asks for the average deal size per employee.",
                "tip": "Use **AVG(amount)** grouped by **employee_id**.",
                "task": "Show **employee_id** and their **AVG(amount)** (average sale amount).",
                "expected": "SELECT employee_id, AVG(amount) FROM sales GROUP BY employee_id;"
            },
            {
                "story": "🏷️ The HR manager wants to know which manager handles which departments.",
                "tip": "Group by the **manager** column, and use **COUNT(\*)** to count departments.",
                "task": "Show **manager** and the **COUNT(\*)** of departments they manage.",
                "expected": "SELECT manager, COUNT(*) FROM departments GROUP BY manager;"
            },
            {
                "story": "💰 The finance team needs to know the highest salary in each department.",
                "tip": "Use the **MAX(salary)** aggregate function and **GROUP BY department_id**.",
                "task": "Show **department_id** and the **MAX(salary)** in that department.",
                "expected": "SELECT department_id, MAX(salary) FROM employees GROUP BY department_id;"
            }
        ],
        "HAVING": [
            {
                "story": "💰 The CEO wants to see departments where the average salary is over 500,000.",
                "tip": "Use the **HAVING** clause to filter the result of the aggregate function: **HAVING AVG(salary) > 500000**.",
                "task": "Show **department_id** and **AVG(salary)** where AVG(salary) **> 500000**.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id HAVING AVG(salary) > 500000;"
            },
            {
                "story": "📦 The sales director wants to see products that generated more than 15,000 total revenue.",
                "tip": "Apply the filter on the total amount: **HAVING SUM(amount) > 15000**.",
                "task": "Show **product** and **SUM(amount)** where SUM(amount) **> 15000**.",
                "expected": "SELECT product, SUM(amount) FROM sales GROUP BY product HAVING SUM(amount) > 15000;"
            },
            {
                "story": "🧾 HR wants departments that have more than one employee.",
                "tip": "Filter the count: **HAVING COUNT(*) > 1**.",
                "task": "Show **department_id** and **COUNT(\*)** where COUNT(\*) **> 1**.",
                "expected": "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id HAVING COUNT(*) > 1;"
            },
            {
                "story": "📈 The CEO wants employees who have made more than one sale.",
                "tip": "Group by employee ID, then use **HAVING COUNT(*) > 1**.",
                "task": "Show **employee_id** and **COUNT(\*)** of sales where COUNT(\*) **> 1**.",
                "expected": "SELECT employee_id, COUNT(*) FROM sales GROUP BY employee_id HAVING COUNT(*) > 1;"
            },
            {
                "story": "💸 The finance team only wants to see departments whose total salary is at least 1,000,000.",
                "tip": "Use **SUM()** and the greater-than-or-equal operator: **HAVING SUM(salary) >= 1000000**.",
                "task": "Show **department_id** and **SUM(salary)** where SUM(salary) **>= 1000000**.",
                "expected": "SELECT department_id, SUM(salary) FROM employees GROUP BY department_id HAVING SUM(salary) >= 1000000;"
            },
            {
                "story": "🎯 The marketing team only cares about employees who have average sales above 12,000.",
                "tip": "Use the **AVG()** function in the **HAVING** clause: **HAVING AVG(amount) > 12000**.",
                "task": "Show **employee_id** and **AVG(amount)** where AVG(amount) **> 12000**.",
                "expected": "SELECT employee_id, AVG(amount) FROM sales GROUP BY employee_id HAVING AVG(amount) > 12000;"
            },
            {
                "story": "🏢 HR wants to find managers who manage more than one department.",
                "tip": "Group by the **manager**, and filter the counts with **HAVING COUNT(*) > 1**.",
                "task": "Show **manager** and **COUNT(\*)** of departments where COUNT(\*) **> 1**.",
                "expected": "SELECT manager, COUNT(*) FROM departments GROUP BY manager HAVING COUNT(*) > 1;"
            },
            {
                "story": "📉 The finance team needs departments where the minimum salary is below 400,000.",
                "tip": "The required syntax is: **HAVING MIN(salary) < 400000**.",
                "task": "Show **department_id** and **MIN(salary)** where MIN(salary) **< 400000**.",
                "expected": "SELECT department_id, MIN(salary) FROM employees GROUP BY department_id HAVING MIN(salary) < 400000;"
            }
        ]
    }

    # --- Show current task ---
    tasks_list = tasks.get(task_type, [])
    safe_index = min(st.session_state.task_index, len(tasks_list) - 1)
    current_task = tasks_list[safe_index]

    st.subheader(f"🧠 {task_type} Task")
    st.markdown(f"**Story:** {current_task['story']}")
    st.markdown(f"**Task:** {current_task['task']}")

    with st.expander("💡 Hint"):
        st.info(f"**Help:** {current_task['tip']}")
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
            time.sleep(0.5)
            st.session_state.sql_input = ""
            st.rerun()
        else:
            st.info("No more tasks in this type. You can choose another type.")

    st.divider()
    st.subheader(f"🏅 Current Score for {st.session_state.name}: {st.session_state.score}")

# ==================== Instructor MODE ====================
else:
    st.subheader("🔐 Instructor Dashboard")
    password = st.text_input("Enter teacher password:", type="password")

    if password == TEACHER_PASSWORD:
        st.success("Access granted. Welcome, teacher!")
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
