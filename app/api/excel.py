import pandas as pd


class Excel():
    help = 'Import quiz results from Excel file'

    def __init__(self):
        self.xls = None
        self.sheets = None
        self.main_results_sheet = None
        self.user_list = []
        self.question_list = []
        self.question_type_mapping_list = []

    def read_excel_sheets(self, excel_file):
        self.xls = pd.ExcelFile(excel_file, engine='openpyxl')
        self.sheets = self.xls.sheet_names
        self.main_results_sheet = pd.read_excel(self.xls, sheet_name=self.xls.sheet_names[0])

    def get_questions(self):
        print("Getting Questions: Starting...")

        for sheet_name in self.sheets:
            # Skip 'Main results' and 'Wall' sheets
            if sheet_name in ['Main results', 'Wall']:
                continue

            df = pd.read_excel(self.xls, sheet_name=sheet_name)
            num_rows = df.shape[0]
            print(f"Getting Questions: Sheet: {sheet_name}, Number of rows: {num_rows}")

            question = {
                'text': df.columns[0],
                'number': self.sheets.index(sheet_name),
                'answers': []
            }
            is_mcq = False  # Assume that it is Open Question or Poll Type

            # Check if the question is a MCQ by checking if row 3 is 'Choice'
            if df.iloc[1, 0] == 'Choice':
                # Scan for 'Maximum score' and get the value on the right cell
                for i in range(num_rows):
                    if df.iloc[i, 0] == 'Maximum score':
                        question['max_score'] = df.iloc[i, 1]
                        print(f"Getting Questions: MCQ Type as max_score is found")
                        break

                if 'max_score' not in question:
                    continue

                self.question_type_mapping_list.append({'sheet_name': sheet_name, 'is_mcq': True})
                is_mcq = True

            # Get the answer options if it is a MCQ
            if is_mcq:
                question['answers'] = []
                for j in range(2, num_rows):
                    if pd.isnull(df.iloc[j, 0]):
                        break
                    question['answers'].append({'text': df.iloc[j, 0], 'is_correct': False})
                self.question_list.append(question)
                print(f"Getting Questions: Max score: {question['max_score']}, Number of answer options: {len(question['answers'])}")
            else:
                self.question_type_mapping_list.append({'sheet_name': sheet_name, 'is_mcq': False})
                print("Getting Questions: Open Question or Poll Type, Skipping")

        print("Getting Questions: Completed!\n")
        return self.question_list

    def get_users(self):
        print("Getting Users: Starting...")
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
        print("Getting Users: Completed! \n")
        return self.user_list

    def get_user_answer_attempts(self, email):
        print(f"Getting Answer Attempts: {email}...")
        user_answer_attempt_list = []
        i = 0

        # Create a list of indices for columns that are MCQ
        mcq_indices = [
            idx for idx in range(5, len(self.main_results_sheet.columns) - 1)
            if idx - 5 < len(self.question_type_mapping_list) and self.question_type_mapping_list[idx - 5]['is_mcq']
        ]
        print(f"Getting Answer Attempts: MCQ Indices (Columns): {mcq_indices}")

        try:
            # Scan each row in main result sheet
            while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
                # If the email matches
                if self.main_results_sheet.iloc[i, 4].upper() == email.upper():
                    print(f"Getting Answer Attempts: Found {email}")

                    # Iterate through each MCQ question to the end of the columns
                    for j in mcq_indices:
                        user_question_attempt = {}
                        wooclap_selected_answer_string = self.main_results_sheet.iloc[i, j]

                        # Check if the first character is '/'
                        if wooclap_selected_answer_string[0] == '/':
                            # User did not attempt the question
                            print(f"Getting Answer Attempts: {email} did not attempt question {j - 5 + 1}")
                        else:
                            # Get characters after the first 4 characters
                            wooclap_selected_answer_string = wooclap_selected_answer_string[4:]
                            print(f"Getting Answer Attempts: {email} attempted question {j - 5 + 1}, options "
                                  f"selected: {wooclap_selected_answer_string}")

                        # Ensure the question index is within bounds
                        if j - 5 < len(self.question_list):
                            user_question_attempt['question'] = self.question_list[j - 5]['text']
                            user_question_attempt['selected_answers'] = [
                                answer['text'] for answer in self.question_list[j - 5]['answers']
                                if answer['text'] in wooclap_selected_answer_string.split(', ')
                            ]
                            # Log selected answers
                            for answer in user_question_attempt['selected_answers']:
                                print(f"Getting Answer Attempts: {email} selected answer: {answer}")
                            user_answer_attempt_list.append(user_question_attempt)

                        else:
                            print(f"Getting Answer Attempts: Question index {j - 5 + 1} out of bounds")
                i += 1
        except Exception as e:
            print(f"Getting Answer Attempts: Error getting {email} Answer Attempts: {str(e)}")


        print(f"Getting {email} Answer Attempts...Complete!\n")
        return user_answer_attempt_list
