import sqlite3
import random
import string
import uuid


def generate_group_code():
    return str(uuid.uuid4())


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        connection = self.get_connection()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
            meet_id INTEGER,
            group_id TEXT,
            date TEXT,
            duration INTEGER,
            name TEXT,
            description TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, 
            calendar_id TEXT,
            group_id TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
            group_id TEXT,
            admin_id INTEGER,
            name TEXT,
            group_code TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
            meet_id INTEGER,
            calendar_event_id TEXT
            )
            """
        )
        connection.commit()
        connection.close()

    def delete_database(self):
        connection = self.get_connection()
        c = connection.cursor()
        c.execute("DROP TABLE IF EXISTS meetings")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS groups")
        connection.commit()
        connection.close()

    def insert_group_meeting(
        self, meet_id, group_id, date, duration, name, description
    ):
        """
        Важно: смотреть на формат date!
        :param meet_id: int
        :param group_id: str
        :param date: str, format '%Y-%m-%d %H:%M:%S'
        :param duration: int, minutes
        :param name: str
        :param description: str
        :return: none
        """
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO meetings "
            "(meet_id, group_id, date, duration, name, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (meet_id, group_id, date, duration, name, description),
        )
        connection.commit()
        connection.close()

    def insert_calendar_event_id(self, meet_id, calendar_event_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO calendar_events "
            "(meet_id, calendar_event_id) "
            "VALUES (?, ?)",
            (meet_id, calendar_event_id),
        )
        connection.commit()
        connection.close()

    def insert_user(self, user_id, calendar_id, group_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users "
            "(user_id, calendar_id, group_id) "
            "VALUES (?, ?, ?)",
            (user_id, calendar_id, group_id),
        )
        connection.commit()
        connection.close()

    def insert_group(self, group_id, member_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO groups " "(group_id) " "VALUES (?)",
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

    def update_user_group(self, user_id, new_group_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        # Update the group_id for the user
        cursor.execute(
            "UPDATE users SET group_id = ? WHERE user_id = ?", (new_group_id, user_id)
        )
        connection.commit()
        connection.close()

    def update_user_calendar_id(self, user_id, new_calendar_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        # Update the calendar_id for the user
        cursor.execute(
            "UPDATE users SET calendar_id = ? WHERE user_id = ?",
            (new_calendar_id, user_id),
        )
        connection.commit()
        connection.close()

    def create_group(self, group_name, admin_id):
        group_id = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=10)
        )  # Уникальный ID группы
        group_code = (
            generate_group_code()
        )  # 32 шестнадцатеричных цифры - секретный код для входа в группу

        connection = self.get_connection()
        connection.execute(
            """
            INSERT INTO groups (group_id, admin_id, name, group_code) 
            VALUES (?, ?, ?, ?)
        """,
            (group_id, admin_id, group_name, group_code),
        )
        connection.commit()
        connection.close()

        return group_id, group_code

    def get_user_group_id(self, user_id: int):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT group_id FROM users WHERE user_id = ?", (user_id,))
        group_id = cursor.fetchone()

        connection.close()
        return group_id[0] if group_id else None

    def join_group(self, user_id, group_code):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT group_id FROM groups WHERE group_code = ?", (group_code,)
        )
        group_id = cursor.fetchone()

        if group_id:
            group_id = group_id[0]

            cursor.execute(
                "INSERT INTO users (user_id, calendar_id, group_id) VALUES (?, ?, ?)",
                (user_id, "", group_id),
            )
            connection.commit()
            connection.close()

            return group_id
        else:
            connection.close()
            return None

    def get_users_and_calendar_ids_in_same_group(self, user_id: int):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT group_id FROM users WHERE user_id = ?", (user_id,))
        group_id = cursor.fetchone()
        group_id = group_id[0]

        all_users_in_groups = set()
        cursor.execute(
            "SELECT user_id, calendar_id FROM users WHERE group_id = ?", (group_id,)
        )
        users_calendar_data = cursor.fetchall()

        connection.close()
        return list(users_calendar_data)


if __name__ == "__main__":
    db = Database("meetings.db")
    # print(db.get_users_id_in_group(403015108))
