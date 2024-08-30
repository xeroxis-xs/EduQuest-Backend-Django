import pandas as pd


class Excel():
    help = 'Import quiz results from Excel file'

    def __init__(self):
        self.xls = None
        self.sheets = None
        self.main_results_sheet = None
        self.question_list = []
        self.user_list = []
        self.question_list = []
        self.question_type_mapping_list = []

    def read_excel_sheets(self, excel_file):
        self.xls = pd.ExcelFile(excel_file, engine='openpyxl')
        self.sheets = self.xls.sheet_names
        self.main_results_sheet = pd.read_excel(self.xls, sheet_name=self.xls.sheet_names[0])

    def get_questions(self):
        # print("Getting Questions")

        for sheet_name in self.sheets:
            # Skip 'Main results' and 'Wall' sheets
            if sheet_name in ['Main results', 'Wall']:
                continue

            df = pd.read_excel(self.xls, sheet_name=sheet_name)
            num_rows = df.shape[0]
            # print(f"Sheet: {sheet_name}, Number of rows: {num_rows}")

            question = {
                'text': df.columns[0],
                'number': self.sheets.index(sheet_name),
                'answers': []
            }
            is_mcq = False

            # Check if the question is a MCQ checking if row 3 is 'Choice'
            # MCQ would display 'Choice' instead of 'Answer'
            if df.iloc[1, 0] == 'Choice':
                # Scan for 'Maximum score' and get the value on the right cell
                for i in range(num_rows):
                    if df.iloc[i, 0] == 'Maximum score':
                        question['max_score'] = df.iloc[i, 1]
                        break

                if 'max_score' not in question:
                    raise Exception(f"Maximum score not found for question {sheet_name}")

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
                # print(f"Max score: {question['max_score']}, Number of answer options: {len(question['answers'])}\n")
            else:

                self.question_type_mapping_list.append({
                    'sheet_name': sheet_name,
                    'is_mcq': False
                })
                # print("Open Question or Poll Type, Skipping\n")
        return self.question_list

    def get_users(self):
        i = 0
        while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
            user = dict()
            user['email'] = self.main_results_sheet.iloc[i, 4].upper()
            user['username'] = self.main_results_sheet.iloc[i, 1]
            i += 1
            self.user_list.append(user)
        return self.user_list

    def get_user_question_attempts(self, email):
        user_question_attempt_list = []
        i = 0
        # Scan each row in main result sheet
        while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
            # If the email matches
            if self.main_results_sheet.iloc[i, 4].upper() == email.upper():
                # Create a list of indices for columns that are MCQ
                mcq_indices = [i for i in range(5, len(self.main_results_sheet.columns) - 1) if
                               self.question_type_mapping_list[i - 5]['is_mcq']]
                # Iterate through each mcq question to the end of the columns
                for j in mcq_indices:
                    user_question_attempt = dict()
                    wooclap_selected_answer_string = self.main_results_sheet.iloc[i, j]
                    # Check if the first character is '/'
                    if wooclap_selected_answer_string[0] == '/':
                        # User did not attempt the question
                        print(f"wooclap_selected_answer_string: 'None'")
                    else:
                        # Get characters after the first 4 characters
                        wooclap_selected_answer_string = wooclap_selected_answer_string[4:]
                        print(f"wooclap_selected_answer_string: {wooclap_selected_answer_string}")

                    user_question_attempt['question'] = self.question_list[j - 5]['text']
                    user_question_attempt['selected_answers'] = []
                    # Iterate through each answer string
                    for answer in self.question_list[j - 5]['answers']:
                        # Check if the answer is in the selected answers
                        # E.g. If answer options are is 'Range', 'Inter-quartile Range', 'Mean', 'Median',
                        # and the user selected 'Range', 'Range' will be appended to the selected answers
                        # 'Inter-quartile Range' will not be appended
                        if answer['text'] in wooclap_selected_answer_string.split(', '):
                            print(f"Confirm selected answer: {answer['text']}")
                            user_question_attempt['selected_answers'].append(answer['text'])

                    user_question_attempt_list.append(user_question_attempt)
            i += 1
        # # Export to JSON
        # with open('questions.json', 'w') as f:
        #     json.dump(user_question_attempt_list, f)
        return user_question_attempt_list
