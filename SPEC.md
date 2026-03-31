# hw8
I'm building a command-line Python quiz app with a local login system that reads questions from a JSON file, quizzes users, tracks scores and performance statistics securely (in a non-human-readable format), allows users to provide feedback on questions to influence future quiz selections, and saves results.

User experience:
The app greets the user and gives a short description on what it is and does. It then asks the user what difficulty of questions they want. Then questions are randomly selected from the question bank and the user completes them. There are true and false questions, multiple choice questions, and short answer questions. The following are some examples. True or False: && functions the same as 'and' in python.
Multiple choice: What keyword defines a function? a. func b. define c. def d. function
Short answer: What built-in function returns the length of a string? 'len'


The questions should be in a JSON format as the following: 

  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics"
      "difficulty": "Easy"
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures"
      "difficulty": "Medium"
    }]

Valid responses are as follows: (multiple choice) 'A', 'a', 'B', 'b', 'C', 'c', 'D', 'd'
(True or false) 'True', 'true', 't', 'False', 'false', 'f'
(Short answer) Must be lowercase or camelCase depending on the question.
Make these response formats known to the user. 
If the response is invalid, send the list of valid responses for the question type they're answering. (Doesn't apply to short answer, they only get one chance)

Correct answers output "Correct!" before moving to the next question.
Answers are revealed after incorrect guesses before moving to the next question.

Below are the required features:

A local login system that prompts users for a username and password (or allows them to enter a new username and password). The passwords should not be easily discoverable.

A score history file that tracks performance and other useful statistics over time for each user. This file should not be human-readable and should be relatively secure. (This means someone could look at the file and perhaps find out usernames but not passwords or scores.)

Users should somehow be able to provide feedback on whether they like a question or not, and this should inform what questions they get next. (too hard/too easy will decrease/increase the difficulty if possible.)

The questions should exist in their own human-readable .json file so that they can be easily modified.

Each difficulty should contain 9 questions, 3 of each type. The user will complete 6 questions per session.

Create a challenge mode difficulty only after the user scores perfectly, 6/6, on the hard difficulty. The hard difficulty has 4 questions with two parts. An example would be to determine the output of a print statement (short answer/multiple choice) and then see a new print statement and determine if it crashed what type of error it'd have or if it'd run. (multiple choice/true false)


If there is any more information you want to clear up before building, ask me and we will audit and create a plan for any features, formatting, and so forth.