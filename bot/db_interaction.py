import sqlite3
import matplotlib.pyplot as plt
import datetime

import sqlite3


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        connection = self.get_connection()
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS meetings (
            meet_id INTEGER,
            admin_id TEXT,
            date TEXT,
            duration INTEGER,
            name TEXT,
            description TEXT
            )
            '''
        )
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
            user_id TEXT, 
            meet_id INTEGER, 
            calendar_id TEXT,
            group_id TEXT
            )
            '''
        )
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS groups (
            group_id TEXT,
            member_id TEXT
            )
            '''
        )
        connection.commit()
        connection.close()

    def delete_database(self):
        connection = self.get_connection()
        c = connection.cursor()
        c.execute('DROP TABLE IF EXISTS meetings')
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('DROP TABLE IF EXISTS groups')
        connection.commit()
        connection.close()

    def insert_meeting(self, meet_id, admin_id, date, duration, name, description):
        '''
        Важно: смотреть на формат date!
        :param meet_id: int
        :param admin_id: str
        :param date: str, format '%Y-%m-%d %H:%M:%S'
        :param duration: int, minutes
        :param name: str
        :param description: str
        :return: none
        '''
        connection = self.get_connection()
        connection.execute(
            "INSERT INTO meetings "
            "(meet_id, admin_id, date, duration, name, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (meet_id, admin_id, date, duration, name, description))
        connection.commit()
        connection.close()

    def insert_user(self, user_id, meet_id, calendar_id, group_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users "
            "(user_id, meet_id, calendar_id, group_id) "
            "VALUES (?, ?, ?, ?)",
            (user_id, meet_id, calendar_id, group_id),
        )
        connection.commit()
        connection.close()

    def insert_group(self, group_id, member_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO groups "
            "(group_id, member_id) "
            "VALUES (?, ?)",
            (group_id, member_id),
        )
        connection.commit()
        connection.close()

    def get_calendar_id(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT calendar_id FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        connection.close()
        return row[0] if row else None


if __name__ == '__main__':
    db = Database('meetings.db')
    db.init_db()