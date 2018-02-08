import sqlite3
import time
from operator import itemgetter
from datetime import (datetime, timedelta)

# IF THIS .PY FILE WAS RUN BY MISTAKE
if __name__ == '__main__':
    print('This .py file is additional and should not be executed. Execute "ReminderBotC.py" instead. For help use -help argument.')

def CheckIfOlderThenXMinutes(delay, year, month, day, hour, minute, tzone):
    """Checks if encrypted in <year.month.day hour:minute> datetime is older then 30 minutes ago - returns 1 if older"""
    note_datetime = datetime(year, month, day, hour, minute)
    ts = time.time()
    server_tz = round((datetime.fromtimestamp(ts) -
                  datetime.utcfromtimestamp(ts)).total_seconds()/3600)
    now_time = datetime.now() + timedelta(hours=tzone-server_tz)
    time_delta = round((now_time - note_datetime).total_seconds() / 60)
    if time_delta <= delay:
        return False

    return True


def ConnectToDB(db_file_name, isolation_level):
    """Connecting to an SQLite DB in the file <db_file_name> and returning the connection"""
    try:
        new_connection = sqlite3.connect(db_file_name)
        new_connection.isolation_level = isolation_level
        return new_connection
    except sqlite3.Error as e:
        print('Error opening DB in file "' + db_file_name + '": ' + e.args[0])
        return -1


def CloseConnectionToDB(db_connection):
    """Closing connection to an opened DB"""
    db_connection.close()
    return 0


def CheckSourceStateAndTimezone(source_id, db_connection):
    """Checking the state of a source with <source_id> in DB with db_connection"""
    try:
        # ACQUIRING SOURCE STATE
        cursor = db_connection.cursor()
        cursor.execute('''SELECT STATE, TZONE FROM Sources WHERE SOURCE=?''', (str(source_id),))
    except sqlite3.Error as e:
        print('Error searching source through DB connection: ' + e.args[0])
        return -1

    states = cursor.fetchall()
    if states is None or len(states) == 0:
        return -2

    if len(states) > 1:
        return -3

    return states[0]


def GetSourceLanguage(source_id, db_connection):
    """Getting language of a source with <source_id> in DB with db_connection"""
    try:
        # ACQUIRING SOURCE LANGUAGE
        cursor = db_connection.cursor()
        cursor.execute('''SELECT LANG FROM Sources WHERE SOURCE=?''', (str(source_id),))
    except sqlite3.Error as e:
        print('Error searching source through DB connection: ' + e.args[0])
        return -1

    laguage = cursor.fetchall()
    if laguage is None or len(laguage) == 0:
        return -2

    if len(laguage) > 1:
        return -3

    return laguage[0][0]


def AddSource(source_id, db_connection, is_user, language='eng'):
    """Adding a source with <source_id> to the <db_connection> table"""
    if is_user:
        source_type = 1
    else:
        source_type = 2
    try:
        # ADDING NEW VALUE
        cursor = db_connection.cursor()
        cursor.execute('''INSERT INTO Sources (TYPE, SOURCE, STATE, LANG, TZONE) VALUES (?, ?, ?, ?, ?)''',
                       (source_type, str(source_id), 0, language, 0))
        cursor.execute('''UPDATE Statistics SET TOTALS = (SELECT TOTALS FROM Statistics WHERE ID = 1) + 1 WHERE ID=1''')
    except sqlite3.Error as e:
        print('Error adding a source through DB connection: ' + e.args[0])
        return 1

    return 0


def CommitDBChanges(db_connection):
    """Committing changes to the DB througn the <db_connection>"""
    try:
        # ADDING NEW VALUE
        if db_connection.isolation_level != None:
            db_connection.commit()
    except sqlite3.Error as e:
        print('Error committing changes through DB connection: ' + e.args[0])
        return 1

    return 0


def ChangeSourceState(source_id, db_connection, new_state):
    """ Changing the source <source_id> state to <new_state>"""
    try:
        # CHANGING STATE VALUE
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE Sources SET STATE = ? WHERE SOURCE = ?''', (new_state, str(source_id)))
    except sqlite3.Error as e:
        print('Error changing a source state through DB connection: ' + e.args[0])
        return 1

    return 0


def ChangeSourceTimezone(source_id, db_connection, new_timezone):
    """ Changing the source <source_id> timezone to <new_timezone>"""
    try:
        # CHANGING TIMEZONE VALUE
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE Sources SET TZONE = ? WHERE SOURCE = ?''', (new_timezone, str(source_id)))
    except sqlite3.Error as e:
        print('Error changing a source timezone through DB connection: ' + e.args[0])
        return 1

    return 0


def GetAllNotesOfSource(source_id, db_connection):
    """Getting all notes of the source <source_id> througn <db_connection>"""
    try:
        # ACQUIRING SOURCE NOTES
        cursor = db_connection.cursor()
        cursor.execute('''SELECT YEAR, MONTH, DAY, HOUR, MINUTE, TEXT, REMINDED FROM Notes WHERE SOURCE=?''', (str(source_id),))
    except sqlite3.Error as e:
        print('Error getting notes through DB connection: ' + e.args[0])
        return -1

    notes = cursor.fetchall()
    new_notes = []
    old_notes = []
    for note in notes:
        if note[6] == 0:
            new_notes.append(note)
        else:
            old_notes.append(note)

    # SORTING FROM OLDER TO NEWER
    new_notes.sort(key=itemgetter(0, 1, 2, 3, 4), reverse=False)
    # SORTING FROM NEWER TO OLDER
    old_notes.sort(key=itemgetter(0, 1, 2, 3, 4), reverse=True)
    notes = new_notes + old_notes
    return notes


def GetLastRemindedNoteOfSource(source_id, db_connection):
    """Getting last note of the source <source_id> through <db_connection> that was reminded in last 30 minutes"""
    try:
        # ACQUIRING REMINDED NOTES OF A SOURCE
        cursor = db_connection.cursor()
        cursor.execute('''SELECT ID, YEAR, MONTH, DAY, HOUR, MINUTE, TZONE, TEXT FROM Notes WHERE SOURCE=? AND REMINDED=1''', (str(source_id),))
    except sqlite3.Error as e:
        print('Error getting reminded notes of a source through DB connection: ' + e.args[0])
        return -1

    notes = cursor.fetchall()
    notes.sort(key=itemgetter(1, 2, 3, 4, 5), reverse=True)
    if notes is None or len(notes) == 0:
        return -2
    # REMOVING NOTES, REMINDED LONGER THAN 30 MINUTES AGO
    for note in notes:
        if not CheckIfOlderThenXMinutes(30, note[1], note[2], note[3], note[4], note[5], note[6]):
            return note



def AddNote(source_id, db_connection, year, month, day, hour, minute, tzone, text):
    """Adding a note with date, time and text to the DB through <db_connection>"""
    try:
        cursor = db_connection.cursor()
        cursor.execute('''INSERT INTO Notes (SOURCE, YEAR, MONTH, DAY, HOUR, MINUTE, TZONE, TEXT, REMINDED) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (str(source_id), year, month, day, hour, minute, tzone, text, 0))
        cursor.execute('''UPDATE Statistics SET TOTALN = (SELECT TOTALN FROM Statistics WHERE ID = 1) + 1 WHERE ID=1''')
    except sqlite3.Error as e:
        print('Error saving note through DB connection: ' + e.args[0])
        return 1

    return 0


def DelayNote(note_id, db_connection, year, month, day, hour, minute):
    """Updating the note with <note_id> data and reminded status"""
    try:
        # CHANGING DATE AND REMINDED VALUE
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE Notes SET YEAR=?, MONTH=?, DAY=?, HOUR=?, MINUTE=?, REMINDED=? WHERE ID = ?''',
                       (year, month, day, hour, minute, 0, note_id))
    except sqlite3.Error as e:
        print('Error changing a note data and state through DB connection: ' + e.args[0])
        return 1

    return 0


def GetAllSources(db_file_name, isolation_level=None):
    """Getting all sources from DB in <db_file_name>"""
    try:
        connection = sqlite3.connect(db_file_name)
        connection.isolation_level = isolation_level
        cursor = connection.cursor()
    except sqlite3.Error as e:
        print('Error while opening connection to DB "' + db_file_name + '": ' + e.args[0])
        return -1

    try:
        cursor.execute('''SELECT * FROM Sources''')
        sources = cursor.fetchall()
    except sqlite3.Error as e:
        print('Error while executing SELECT query to DB "' + db_file_name + '": ' + e.args[0])
        return -1

    try:
        connection.close()
    except sqlite3.Error as e:
        print('Error while closing connection to DB "' + db_file_name + '": ' + e.args[0])
        return -1

    return sources


def GetAllNotes(db_file_name, isolation_level=None):
    """Getting all notes from DB in <db_file_name>"""
    try:
        connection = sqlite3.connect(db_file_name)
        connection.isolation_level = isolation_level
        cursor = connection.cursor()
        cursor.execute('''SELECT * FROM Notes''')
        notes = cursor.fetchall()
        connection.close()
        return notes
    except sqlite3.Error as e:
        print('Error while opening DB "' + db_file_name + '", reading all rows from Notes and closing it: ' + e.args[0])
        return -1


def ClearSourcesTable(db_file_name, isolation_level=None):
    """Clearing table "Sources" of DB in <db_file_name> file"""
    try:
        connection = sqlite3.connect(db_file_name)
        connection.isolation_level = isolation_level
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM Sources''')
        connection.close()
        return 0
    except sqlite3.Error as e:
        print('Error while opening DB "' + db_file_name + '", clearing Sources table and closing it: ' + e.args[0])
        return 1


def ClearNotesTable(db_file_name, isolation_level=None):
    """Clearing table "Notes" of DB in <db_file_name> file"""
    try:
        connection = sqlite3.connect(db_file_name)
        connection.isolation_level = isolation_level
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM Notes''')
        connection.close()
        return 0
    except sqlite3.Error as e:
        print('Error while opening DB "' + db_file_name + '", clearing Notes table and closing it: ' + e.args[0])
        return 1


def GetNotesToRemind(db_connection):
    """Getting all notes from Notes table of BD from <db_connection> where Reminded is 0 and time is in past"""
    try:
        # ACQUIRING NOTES
        cursor = db_connection.cursor()
        cursor.execute('''SELECT ID, SOURCE, YEAR, MONTH, DAY, HOUR, MINUTE, TZONE, TEXT FROM Notes WHERE REMINDED=0''')
    except sqlite3.Error as e:
        print('Error getting notes through DB connection: ' + e.args[0])
        return -1

    notes = cursor.fetchall()
    notes.sort(key=itemgetter(1, 2, 3, 4, 5, 6), reverse=False)
    if notes is None:
        return -2
    else:
        return notes


def ChangeNotesToReminded(db_connection, notes_ids):
    """Changing all notes with ID from <notes_ids> REMINDED to 1"""
    try:
        # ACQUIRING NOTES
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE Notes SET REMINDED = 1 WHERE ID IN (''' + notes_ids + ''')''')
    except sqlite3.Error as e:
        print('Error getting notes through DB connection: ' + e.args[0])
        return 1

    return 0


def RemoveOldRemindedNotes(db_connection):
    """Removing all notes with REMINDED = 1 and time older then 30 minutes ago from DB from <db_connection>"""
    try:
        # ACQUIRING NOTES
        cursor = db_connection.cursor()
        cursor.execute('''SELECT ID, YEAR, MONTH, DAY, HOUR, MINUTE, TZONE FROM Notes WHERE REMINDED=1''')
    except sqlite3.Error as e:
        print('Error getting old notes through DB connection: ' + e.args[0])
        return -1

    notes = cursor.fetchall()
    count = 0
    if notes is not None:
        notes_id = ''
        for note in notes:
            if CheckIfOlderThenXMinutes(30, note[1], note[2], note[3], note[4], note[5], note[6]):
                notes_id += str(note[0]) + ', '
                count += 1

        if len(notes_id) > 0:
            notes_id = notes_id[0:-2]
            try:
                cursor.execute('''DELETE FROM Notes WHERE ID IN (''' + notes_id + ''')''')
            except sqlite3.Error as e:
                print('Error deleting old notes through DB connection: ' + e.args[0])
                return -1

    return count


def GetStats(db_file_name, isolation_level=None):
    """Getting all statistics from DB in <db_file_name>"""
    try:
        connection = sqlite3.connect(db_file_name)
        connection.isolation_level = isolation_level
        cursor = connection.cursor()
        cursor.execute('''SELECT * FROM Statistics''')
        stats = cursor.fetchall()
        connection.close()
        return stats
    except sqlite3.Error as e:
        print('Error while opening DB "' + db_file_name + '", reading all rows from Statistics and closing it: ' + e.args[0])
        return -1
