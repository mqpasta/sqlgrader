import pyodbc
import re
import os
import csv
import sys

def read_solution_quries(filename):
    solutions = {}
    with open(filename, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file, skipinitialspace=True)
        for row in csv_reader:
            question = row['question']
            query = row['query']
            solutions[question] = query
    return solutions

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
            question_num = f'q{match[0]}'
            query = match[1].strip()
            queries[question_num] = query
    return queries

# Function to execute student SQL queries and compare results
def execute_and_grade(queries, correct_results, conn):
    cursor = conn.cursor()
    grades = {}
    errors = {}
    for question, query in queries.items():
        try:
            if len(query) == 0:
                grades[question] = 'Not Attempted'
                continue
            cursor.execute(query)
            student_result = cursor.fetchall()
            if student_result == correct_results.get(question):
                grades[question] = 'Correct'
            else:
                grades[question] = 'Incorrect'
                errors[question] = f'Expected {correct_results.get(question)} \n got {student_result}'
        except Exception as e:
            grades[question] = f'Error'
            errors[question] = f'Error: {e}'
    return grades, errors

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
            print(f'Processing {file_name}...')
            file_path = os.path.join(directory, file_name)
            # Assuming student name is the second last part of the file name
            student_name = file_name.split('_')[-2]  
            # Assuming student ID is the last part of the file name
            student_id = file_name.split('_')[-1]    

            student_queries = extract_queries(file_path)  # Extract student's SQL queries
            grades, errors = execute_and_grade(student_queries, correct_results, conn)  # Grade student submission
            write_grades(student_name, student_id, grades)  # Write grades to file
            if len(errors) > 0:
                with open("errors/"+file_name+".log", 'a') as file:
                    for question, error in errors.items():
                        file.write(f'{question}: {error}\n')
                    file.write('\n')

    conn.close()

def generate_output_file(output_file='grades.txt', questions=['Q1', 'Q2']):
    with open(output_file, 'w') as file:
        file.write('Name,ID,')
        file.write(','.join(questions))
        file.write('\n')

def create_error_directory(directory):
    if not os.path.exists(directory):
        print(f"Creating directory {directory}")
        os.makedirs(directory)

# Example usage
if __name__ == '__main__':
    directory = 'submissions'
    server = '.\SQLEXPRESS'
    database = 'eis'
    solution = 'solutions.csv'
    error_directory = 'errors'

    for index,arg in enumerate(sys.argv):
        print(f"Argument {index}: {arg}")
    
    create_error_directory(error_directory)
    correct_answers = read_solution_quries(solution)
    
    generate_output_file(questions=correct_answers.keys())

    process_all_submissions(directory, correct_answers, server, database)
