import re

# IF THIS .PY FILE WAS RUN BY MISTAKE
if __name__ == '__main__':
    print('This .py file is additional and should not be executed. Execute "ReminderBotC.py" instead. For help use -help argument.')

def CheckForDateTimeText(input):
    """Check input text to match pattern via regular expressions"""
    pattern1 = r""" *[1-2][0-9]{3}\.[0-1][0-9]\.[0-3][0-9] *[0-2][0-9]:[0-5][0-9] .*"""
    pattern2 = r""" *[0-2][0-9]:[0-5][0-9] .*"""
    if re.match(pattern1, input, re.DOTALL) is not None:
        return 1
    if re.match(pattern2, input, re.DOTALL) is not None:
        return 2

    return 0


def CheckForDateTimeOrTime(input):
    """Check input text to match pattern via regular expressions. Done by Brunman Mikhail <Taimish> (c) 2018 RF"""
    pattern1 = r""" *[1-2][0-9]{3}\.[0-1][0-9]\.[0-3][0-9] *[0-2][0-9]:[0-5][0-9] *"""
    pattern2 = r""" *[0-2][0-9]:[0-5][0-9] *"""
    if re.match(pattern1, input) is not None:
        return 1
    if re.match(pattern2, input) is not None:
        return 2

    return 0


def CheckForRemindFormat(input):
    """Check input text to match pattern via regular expressions."""
    #pattern = r"""\s*(\d{1,2}\s+){1,5}\s+[a-zA-Z]{1}[a-zA-Z ]{2}"""
    pattern1 = r'\s*\d{1,2}\s+[^\d\s]{3}'
    pattern2 = r'\s*\d{1,2} +\d{1,2}\s+[^\d\s]{3}'
    pattern3 = r'\s*\d{1,2} +\d{1,2} +\d{1,2}\s+[^\d\s]{3}'
    pattern4 = r'\s*\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2}\s+[^\d\s]{3}'
    pattern5 = r'\s*\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2} +\d{1,4}\s+[^\d\s]{3}'

    if re.match(pattern1, input) is not None:
        return 1

    if re.match(pattern2, input) is not None:
        return 2

    if re.match(pattern3, input) is not None:
        return 3

    if re.match(pattern4, input) is not None:
        return 4

    if re.match(pattern5, input) is not None:
        return 5

    return 0
