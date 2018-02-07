ReminderBotC project

A console-oriented version of ReminderBot project.
This project contains python3 script files for a reminder telegram bot, whos aim is to save and remind notes for users.

Baisicaly it contains four *.py files. The ReminderBot.py file contains the main bot code.
Other three files contains some specified functions for bot to work (HTTP transfer functions, SQL query functions, regular expression check functions).
Also the project contains a venv directiory with virtual environment for project to run and a pycache directory with caches.

For project to work properly you need to add next information to a file bot.info in project directory.
First line should contain telegram bot token.
Second line should contain update number (at start it can be -102 to get all updates and calculate actual update number).

Python 3.5 project.
Used packages:
pip	V9.0.1
setuptools 	V38.4.0
sip	V4.19.6
wheel	V0.30.0 

Projects start from terminal.

It can be run without any arguments, which leads to a cycle, where an information with available commands is listed and any command can be inputed.

Brunman Mikhail -Taimish- (c) 2018
