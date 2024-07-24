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
        self.user_quest_attempt_list = []
        self.user_question_attempt_list = []

    def handle(self, *args, **kwargs):
        self.read_excel_sheets()
        self.get_questions()
        # self.get_users()
        # self.get_user_quest_attempts()
        self.get_user_question_attempts("C210101@e.ntu.edu.sg")

    def read_excel_sheets(self):
        excel_file = 'app/api/management/commands/JBRYGU_Introduction_to_Database_-_Quiz_1-results.xlsx'
        self.xls = pd.ExcelFile(excel_file, engine='openpyxl')
        self.sheets = self.xls.sheet_names
        self.main_results_sheet = pd.read_excel(self.xls, sheet_name=self.xls.sheet_names[0])

    def get_questions(self):
        for i in range(len(self.sheets)):
            if self.sheets[i] != 'Main results' and self.sheets[i] != 'Wall':
                # print(f"Sheet name: {self.sheets[i]}")
                question = dict()
                df = pd.read_excel(self.xls, sheet_name=self.xls.sheet_names[i])
                question['text'] = df.head(0).columns[0].strip()
                question['number'] = i
                # print(f"Question text: {question['text']}")
                question['answers'] = []

                j = 2
                while not pd.isnull(df.iloc[j, 0]):
                    answer = dict()
                    answer['text'] = df.iloc[j, 0]
                    answer['is_correct'] = False
                    # print(f"Answer: {df.iloc[j, 0]}")
                    question['answers'].append(answer)
                    j += 1

                k = 0
                while df.iloc[k, 0] != 'Maximum score':
                    k += 1
                question['max_score'] = df.iloc[k, 1]
                # print(f"Max Score: {df.iloc[k, 1]}")

                self.question_list.append(question)

        # print(f"Question list: {self.question_list}")

    def get_users(self):
        user = dict()
        i = 0
        while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
            user['email'] = self.main_results_sheet.iloc[i, 4]
            user['username'] = self.main_results_sheet.iloc[i, 1]
            print(f"Email: {user['email']}")
            print(f"Username: {user['username']}")
            self.user_list.append(user)
            i += 1

    def get_user_quest_attempts(self):
        user_quest_attempt = dict()
        i = 0
        while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
            # Email
            user_quest_attempt['user'] = self.main_results_sheet.iloc[i, 4]
            user_quest_attempt['graded'] = False
            user_quest_attempt['time_taken'] = 0
            user_quest_attempt['quest'] = None
            self.user_quest_attempt_list.append(user_quest_attempt)

    def get_user_question_attempts(self, email):
        user_question_attempt_list = []
        i = 0
        print(f"Email: {email}")
        # Scan each row
        while not pd.isnull(self.main_results_sheet.iloc[i, 0]):
            # If the email matches
            if self.main_results_sheet.iloc[i, 4].upper() == email.upper():
                # Iterate through each question

                for j in range(5, len(self.main_results_sheet.columns)-1):
                    user_question_attempt = dict()
                    wooclap_selected_answer = self.main_results_sheet.iloc[i, j]
                    # Split the wooclap_selected_answer to get the answers part
                    _, wooclap_selected = wooclap_selected_answer.split(" - ", 1)

                    user_question_attempt['question'] = self.question_list[j-5]['text']
                    user_question_attempt['selected_answers'] = []
                    # Iterate through each answer string
                    for answer in self.question_list[j-5]['answers']:
                        if answer['text'] in wooclap_selected:
                            user_question_attempt['selected_answers'].append(answer['text'])
                    user_question_attempt_list.append(user_question_attempt)
            i += 1
        print(f"Selected answers: {user_question_attempt_list}")
        return user_question_attempt_list





