<img width="2752" height="1536" alt="Banner" src="https://github.com/user-attachments/assets/80b47d8b-6efa-4c53-9d27-fe2762dd0431" />

🎓 Interactive SQL Training App
Master SQL basics through real-world scenarios! This interactive web application allows students to practice SQL queries in a sandboxed environment and lets teachers track progress in real-time.

🖼️ Preview
Note: Replace this with your actual banner image or a screenshot of your app!

🚀 Features
🧑‍🎓 For Students
Story-Driven Learning: Solve tasks based on real-world business scenarios (HR, Sales, IT).

Instant Feedback: Run queries and see the results immediately in a data table.

Live Visualizations: Automatically generates bar charts for numeric results.

ER Diagrams: Built-in schema viewer using Graphviz to help you understand table relationships.

Progress Tracking: Earn points for every correct answer.

👩‍🏫 For Teachers
Secure Dashboard: Password-protected area to monitor student activity.

Submission Logs: View every query attempted by students, including timestamps and success rates.

Data Export: Download the entire submission history as a CSV for grading or analysis.

🛠️ Tech Stack
Frontend: Streamlit

Database: SQLite3 (In-memory)

Data Handling: Pandas

Diagrams: Graphviz

📋 Database Schema
The app comes pre-loaded with a relational database containing:

Employees: Names, salaries, and hire dates.

Departments: Management and structure.

Sales: Transactional records and products.

Customers: International client data.

⚙️ Installation & Setup
Clone the repository:

Bash
git clone https://github.com/your-username/sql-training-app.git
cd sql-training-app
Install dependencies:

Bash
pip install streamlit pandas graphviz
Run the application:

Bash
streamlit run app.py
🔒 Teacher Access
To access the Teacher Dashboard, use the default password:
sql2025
(You can change this in the TEACHER_PASSWORD variable inside app.py)

🤝 Contributing
Found a bug or want to add more SQL tasks? Feel free to open an issue or submit a pull request!

Happy Querying! 🔍💻
