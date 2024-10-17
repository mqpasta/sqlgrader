import pyodbc
import re
import os

# Connection to the MS SQL Server database (Windows Authentication)
def connect_db(server, database):
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

# Function to execute and store correct answers
def execute_correct_answers(answers, conn):
    correct_results = {}
    cursor = conn.cursor()
    for question, query in answers.items():
        cursor.execute(query)
        result = cursor.fetchall()
        correct_results[question] = result
    return correct_results

# Function to extract student queries from the SQL file
def extract_queries(file_path):
    queries = {}
    with open(file_path, 'r') as file:
        content = file.read()
        matches = re.findall(r'-- Q(\d+):.*?-- Provide your answer below\s+(.*?)(?=\n-- Q\d+:|$)', content, re.DOTALL)
        for match in matches:
            question_num = f'Q{match[0]}'
            query = match[1].strip()
            queries[question_num] = query
    return queries

# Function to execute student SQL queries and compare results
def execute_and_grade(queries, correct_results, conn):
    cursor = conn.cursor()
    grades = {}
    for question, query in queries.items():
        try:
            cursor.execute(query)
            student_result = cursor.fetchall()
            if student_result == correct_results.get(question):
                grades[question] = 'Correct'
            else:
                grades[question] = 'Incorrect'
        except Exception as e:
            grades[question] = f'Error: {e}'
    return grades

# Function to write grades to a file
def write_grades(student_name, student_id, grades, output_file='grades.txt'):
    output = []
    output.append(student_name)
    output.append(student_id)
    for question, grade in grades.items():
        output.append(f"{grade}")
    with open(output_file, 'a') as file:
        file.write(','.join(output))	# Write grades to file
        file.write("\n")

# Function to process all .sql files in a directory
def process_all_submissions(directory, correct_answers, server, database):
    conn = connect_db(server, database)
    correct_results = execute_correct_answers(correct_answers, conn)  # Store the correct results

    for file_name in os.listdir(directory):
        if file_name.endswith('.sql'):
            file_path = os.path.join(directory, file_name)
            student_name = file_name.split('_')[0]  # Assuming student name is part of the file name
            student_id = file_name.split('_')[1]    # Assuming student ID is part of the file name

            student_queries = extract_queries(file_path)  # Extract student's SQL queries
            grades = execute_and_grade(student_queries, correct_results, conn)  # Grade student submission
            write_grades(student_name, student_id, grades)  # Write grades to file

    conn.close()

def generate_output_file(output_file='grades.txt', questions=['Q1', 'Q2']):
    with open(output_file, 'w') as file:
        file.write('Name,ID,')
        file.write(','.join(questions))
        file.write('\n')

# Example usage
if __name__ == '__main__':
    directory = 'submissions'
    server = '.\SQLEXPRESS'
    database = 'eis'
    
    # Correct answers for comparison
    correct_answers = {
        'Q1': 'SELECT * FROM department;',
        'Q2': "SELECT * FROM bonus;"
    }

    generate_output_file()

    process_all_submissions(directory, correct_answers, server, database)
