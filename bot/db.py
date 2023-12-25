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
            calendar_event_id TEXT,
            calendar_id TEXT
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

    def insert_calendar_event_id(self, meet_id, calendar_event_id, calendar_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO calendar_events "
            "(meet_id, calendar_event_id, calendar_id) "
            "VALUES (?, ?, ?)",
            (meet_id, calendar_event_id, calendar_id),
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

    def get_group_id(self, group_code):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT group_id FROM groups WHERE group_code = ?", (group_code,)
        )
        group_id = cursor.fetchone()

        connection.commit()
        connection.close()
        return group_id

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
        )  # unique group id
        group_code = (
            generate_group_code()
        )  # 32 hexadecimal digits - secret code to enter the group

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

        cursor.execute(
            "SELECT user_id, calendar_id FROM users WHERE group_id = ?", (group_id,)
        )
        users_calendar_data = cursor.fetchall()

        connection.close()
        return list(users_calendar_data)

    def check_if_user_is_group_admin(self, user_id: int):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT group_id FROM groups WHERE admin_id = ?", (user_id,))
        result = cursor.fetchone()

        connection.close()
        return result[0] if result else None

    def check_is_group_event(self, calendar_event_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        # check if calendar_event_id in calendar_events
        cursor.execute(
            "SELECT meet_id FROM calendar_events WHERE calendar_event_id = ?",
            (calendar_event_id,),
        )
        meet_id_result = cursor.fetchone()

        if meet_id_result:
            meet_id = meet_id_result[0]

            cursor.execute(
                "SELECT group_id FROM meetings WHERE meet_id = ?", (meet_id,)
            )
            group_id_result = cursor.fetchone()

            if group_id_result:
                group_id = group_id_result[0]

                cursor.execute(
                    "SELECT admin_id FROM groups WHERE group_id = ?", (group_id,)
                )
                admin_id_result = cursor.fetchone()

                connection.close()
                return admin_id_result[0]

        else:
            connection.close()
            return None

    def get_group_event(self, calendar_event_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT meet_id FROM calendar_events WHERE calendar_event_id = ?",
            (calendar_event_id,),
        )
        meet_id = cursor.fetchone()[0]
        cursor.execute(
            "SELECT calendar_event_id, calendar_id FROM calendar_events WHERE meet_id = ?",
            (meet_id,),
        )
        res = cursor.fetchall()

        connection.close()
        return res










    def get_group_members_emails(self, group_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT calendar_id FROM users WHERE group_id = ?", (group_id,))
        emails = cursor.fetchall()
        connection.close()
        return [email[0] for email in emails]

    def get_user_id_by_calendar_id(self, calendar_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE calendar_id = ?", (calendar_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()
            connection.close()

    def remove_member_by_email(self, admin_id, calendar_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT user_id FROM users WHERE calendar_id = ?", (calendar_id,))
        user_data = cursor.fetchone()

        if user_data:
            user_id = user_data[0]

            cursor.execute("UPDATE users SET group_id = '' WHERE user_id = ?", (user_id,))

            connection.commit()
        else:
            pass
        return True

        connection.close()


    def is_user_in_group(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT group_id FROM users WHERE user_id = ? AND group_id <> ''", (user_id,))
        group_data = cursor.fetchone()

        connection.close()

        return group_data is not None

    def check_group_exists(self, group_code):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups WHERE group_code = ?", (group_code,))
        result = cursor.fetchone()
        connection.close()
        return result[0] > 0

    def get_group_members(self, group_code):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            # Вначале получаем group_id по group_code
            cursor.execute("SELECT group_id FROM groups WHERE group_code = ?", (group_code,))
            group = cursor.fetchone()
            if group:
                group_id = group[0]
                # Затем получаем все user_id, связанные с этим group_id
                cursor.execute("SELECT user_id FROM users WHERE group_id = ?", (group_id,))
                members = cursor.fetchall()
                return [member[0] for member in members]
            else:
                # Если группа с таким кодом не найдена, возвращаем пустой список
                return []
        finally:
            # Убедимся, что курсор и соединение закрываются
            cursor.close()
            connection.close()

    def get_group_members_by_user_id(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT group_id FROM users WHERE user_id = ?", (user_id,))
            user_group_data = cursor.fetchone()

            if user_group_data and user_group_data[0]:
                group_id = user_group_data[0]
                cursor.execute("SELECT user_id FROM users WHERE group_id = ?", (group_id,))
                members = cursor.fetchall()
                return [member[0] for member in members]
            else:
                return []
        finally:
            cursor.close()
            connection.close()

    def get_current_group_id(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT group_id FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()
            connection.close()

    def get_group_code(self, admin_id):
        # Assuming `admin_id` is the ID of the admin of the group
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT group_code FROM groups WHERE admin_id = ?", (admin_id,))
        group_code = cursor.fetchone()
        connection.close()
        return group_code[0] if group_code else None

    def remove_member_from_group_by_uid(self, user_id, group_code):
        connection = self.get_connection()
        cursor = connection.cursor()

        # Получаем group_id по group_code
        cursor.execute("SELECT group_id FROM groups WHERE group_code = ?", (group_code,))
        group_record = cursor.fetchone()
        if not group_record:
            return False  # Группа с таким кодом не найдена

        group_id = group_record[0]

        # Удаляем пользователя из группы в таблице users
        cursor.execute("UPDATE users SET group_id = '' WHERE user_id = ? AND group_id = ?", (user_id, group_id))

        # Удаляем пользователя из списка members_id в таблице groups
        cursor.execute("SELECT members_id FROM groups WHERE group_id = ?", (group_id,))
        members_record = cursor.fetchone()
        if members_record:
            members_list = members_record[0].split(' ')
            if str(user_id) in members_list:
                members_list.remove(str(user_id))
                new_members_id = ' '.join(members_list)
                cursor.execute("UPDATE groups SET members_id = ? WHERE group_id = ?", (new_members_id, group_id))

        connection.commit()
        connection.close()
        return True


if __name__ == "__main__":
    db = Database("db.db")
