from django.core.management.base import BaseCommand
import pandas as pd
import json

class Command(BaseCommand):
    help = 'Import quiz results from Excel file'

    def __init__(self):
        self.xls = None
        self.sheets = None
        self.main_results_sheet = None
        self.question_list = []
        self.user_list = []
        self.question_list = []
        self.question_type_mapping_list = []

    def handle(self, *args, **kwargs):
        self.read_excel_sheets()
        self.get_questions()
        self.get_users()
        # for user in self.user_list:
        #     email = user['email']
        #     self.get_user_question_attempts(email)

    def read_excel_sheets(self):
        print("Reading Excel Sheets")
        excel_file = 'app/api/management/commands/JUQSDR_Tutorial_1-results.xlsx'
        self.xls = pd.ExcelFile(excel_file, engine='openpyxl')
        self.sheets = self.xls.sheet_names
        self.main_results_sheet = pd.read_excel(self.xls, sheet_name=self.xls.sheet_names[0])

    def get_questions(self):
        print("Getting Questions...")

        for sheet_name in self.sheets:
            # Skip 'Main results' and 'Wall' sheets
            if sheet_name in ['Main results', 'Wall']:
                continue

            df = pd.read_excel(self.xls, sheet_name=sheet_name)
            num_rows = df.shape[0]
            print(f"Sheet: {sheet_name}, Number of rows: {num_rows}")

            question = {
                'text': df.columns[0],
                'number': self.sheets.index(sheet_name),
                'answers': []
            }
            is_mcq = False

            # Check if the question is a MCQ checking if row 3 is 'Choice'
            # MCQ would display 'Choice' instead of 'Answer'
            if df.iloc[1, 0] == 'Choice':
                question['max_score'] = df.iloc[2, 1]
                self.question_type_mapping_list.append({'sheet_name': sheet_name, 'is_mcq': True})
                is_mcq = True


            # Get the answer options if it is a MCQ
            if is_mcq:
                j = 2
                while j < num_rows and not pd.isnull(df.iloc[j, 0]):
                    question['answers'].append({
                        'text': df.iloc[j, 0],
                        'is_correct': False
                    })
                    j += 1
                self.question_list.append(question)
                print(f"Max score: {question['max_score']}, Number of answer options: {len(question['answers'])}")
            else:

                self.question_type_mapping_list.append({
                    'sheet_name': sheet_name,
                    'is_mcq': False
                })
                print("Open Question or Poll Type, Skipping")
        print("Getting Questions...Complete!\n")
        return self.question_list

    def get_users(self):
        print("Getting Users...")
        i = 0
        try:
            while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
                user = dict()
                user['email'] = self.main_results_sheet.iloc[i, 4].upper()
                user['username'] = self.main_results_sheet.iloc[i, 1]
                i += 1
                self.user_list.append(user)
        except Exception as e:
            print(f"Error getting users: {str(e)}")
        print("Getting Users...Complete!\n")
        return self.user_list

    def get_user_question_attempts(self, email):
        print(f"Getting {email} Question Attempts...")
        user_question_attempt_list = []
        i = 0
        try:
            # Scan each row in main result sheet
            while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
                # If the email matches
                if self.main_results_sheet.iloc[i, 4].upper() == email.upper():
                    print(f"Found {email} at row {i}")
                    # Create a list of indices for columns that are MCQ
                    mcq_indices = [i for i in range(5, len(self.main_results_sheet.columns) - 1) if
                                   self.question_type_mapping_list[i - 5]['is_mcq']]
                    # Iterate through each mcq question to the end of the columns
                    for j in mcq_indices:
                        user_question_attempt = dict()
                        wooclap_selected_answer = self.main_results_sheet.iloc[i, j]
                        # Split the wooclap_selected_answer to get the answers part
                        split_result = wooclap_selected_answer.split(" - ", 1)
                        if len(split_result) == 2:
                            _, wooclap_selected = split_result
                        else:
                            # Handle the case where the split does not result in exactly 2 elements
                            # When user did not select any answer
                            print("No answer selected")
                            wooclap_selected = []
                        user_question_attempt['question'] = self.question_list[j - 5]['text']
                        user_question_attempt['selected_answers'] = []
                        # Iterate through each answer string
                        for answer in self.question_list[j - 5]['answers']:
                            if answer['text'] in wooclap_selected:
                                user_question_attempt['selected_answers'].append(answer['text'])
                                print(user_question_attempt)

                        user_question_attempt_list.append(user_question_attempt)
                i += 1
        except Exception as e:
            print(f"Error getting {email} question attempts: {str(e)}")
        # Export to JSON
        # Ensure the file is opened in write mode
        with open('questions.json', 'w') as f:
            try:
                # Verify that user_question_attempt_list is correctly populated
                if user_question_attempt_list:
                    json.dump(user_question_attempt_list, f)
                    print("Data successfully written to questions.json")
                else:
                    print("user_question_attempt_list is empty, nothing to write.")
            except Exception as e:
                print(f"Error writing to file: {str(e)}")
        print(f"Getting {email} Question Attempts...Complete!\n")
        return user_question_attempt_list





