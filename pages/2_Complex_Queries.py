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
Choose your mode on the left, and explore **JOINs**, **subqueries**, and **aggregations** step-by-step.
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
                "title": "INNER JOIN alapok",
                "explanation": "Az INNER JOIN csak azokat a sorokat adja vissza, amelyek mindkét táblában megtalálhatók.",
                "visual": "🟦 A ∩ B – csak a közös rész marad meg.",
                "story": "Listázd ki a projektek nevét és az őket kezelő részlegek vezetőjét!",
                "expected": "SELECT p.name AS project, d.manager FROM projects p JOIN departments d ON p.department_id = d.id;"
            },
            {
                "title": "LEFT JOIN – minden bal oldali elem",
                "explanation": "A LEFT JOIN a bal oldali tábla összes sorát visszaadja, akkor is, ha nincs párja a jobb oldalon.",
                "visual": "🟦 A ⟕ B – a bal tábla minden sora + közös találatok.",
                "story": "Listázd ki az összes részleget és a hozzájuk tartozó projekteket (akkor is, ha egy részleghez nincs projekt).",
                "expected": "SELECT d.name AS department, p.name AS project FROM departments d LEFT JOIN projects p ON d.id = p.department_id;"
            },
            {
                "title": "RIGHT JOIN (helyettesítve LEFT JOIN-nel SQLite-ban)",
                "explanation": "A RIGHT JOIN a jobb oldali tábla összes sorát adja vissza. Mivel SQLite-ban nincs RIGHT JOIN, a sorrendet megcseréljük.",
                "visual": "🟦 A ⟖ B – a jobb tábla minden sora + közös találatok.",
                "story": "Listázd a projekteket és a hozzájuk tartozó részlegeket úgy, hogy minden projekt megjelenjen.",
                "expected": "SELECT p.name AS project, d.name AS department FROM departments d LEFT JOIN projects p ON d.id = p.department_id;"
            },
            {
                "title": "FULL OUTER JOIN (helyettesítve UNION-nel)",
                "explanation": "A FULL OUTER JOIN mindkét tábla sorait visszaadja, akkor is, ha nincs párjuk. SQLite-ban UNION-nel szimuláljuk.",
                "visual": "🟦 A ∪ B – minden sor megmarad mindkét táblából.",
                "story": "Listázd ki az összes részleget és projektet (akkor is, ha valamelyiknek nincs párja).",
                "expected": """
                SELECT d.name AS department, p.name AS project 
                FROM departments d LEFT JOIN projects p ON d.id = p.department_id
                UNION
                SELECT d.name AS department, p.name AS project 
                FROM departments d LEFT JOIN projects p ON d.id = p.department_id;
                """
            },
            {
                "title": "💡 Vegyes gyakorló JOIN",
                "explanation": "Itt már nem kapsz segítséget — döntsd el, melyik JOIN típus illik a feladathoz!",
                "visual": "❓ Döntsd el: INNER, LEFT vagy más?",
                "story": "Listázd ki az összes alkalmazottat és az általuk végzett feladatokat, akkor is, ha valakinek még nincs feladata.",
                "expected": "SELECT e.name AS employee, t.status FROM employees e LEFT JOIN tasks t ON e.id = t.assigned_to;"
            }
        ],
        "Subqueries": [
            {
                "title": "Egyszerű al-lekérdezés",
                "explanation": "A subquery a WHERE részben használható másik lekérdezés eredményének szűrésére.",
                "visual": "🌀 Bemeneti szűrés egy másik lekérdezés alapján.",
                "story": "Listázd azokat az alkalmazottakat, akik olyan részlegen dolgoznak, ahol a projektek költségvetése 1 000 000 felett van.",
                "expected": "SELECT name FROM employees WHERE department_id IN (SELECT department_id FROM projects WHERE budget > 1000000);"
            },
            {
                "title": "Subquery SELECT részben",
                "explanation": "Az al-lekérdezés nemcsak WHERE-ben, hanem SELECT részben is használható számításra.",
                "visual": "🧮 Beágyazott számítások egy soronkénti lekérdezésben.",
                "story": "Mutasd meg minden részlegnél a projektek számát!",
                "expected": "SELECT d.name, (SELECT COUNT(*) FROM projects p WHERE p.department_id = d.id) AS project_count FROM departments d;"
            }
        ],
        "Aggregations": [
            {
                "title": "GROUP BY és HAVING gyakorlás",
                "explanation": "A GROUP BY csoportosítja az adatokat, a HAVING pedig szűr a csoportokra.",
                "visual": "Σ összegzés és szűrés csoportonként.",
                "story": "Listázd azokat a részlegeket, ahol az átlagfizetés 600 000 fölött van.",
                "expected": "SELECT department_id, AVG(salary) FROM employees GROUP BY department_id HAVING AVG(salary) > 600000;"
            },
            {
                "title": "📘 Ismétlés – Összetett lekérdezés",
                "explanation": "Ismétlés az első óráról: kombináld a SELECT, FROM, WHERE, GROUP BY, HAVING kulcsszavakat.",
                "visual": "🧩 Minden elem együtt: szűrés, csoportosítás, aggregálás.",
                "story": "Listázd azokat a részlegeket, ahol több mint egy alkalmazott dolgozik és az átlagfizetésük 500 000 felett van.",
                "expected": "SELECT department_id, COUNT(*), AVG(salary) FROM employees WHERE salary > 400000 GROUP BY department_id HAVING COUNT(*) > 1 AND AVG(salary) > 500000;"
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
