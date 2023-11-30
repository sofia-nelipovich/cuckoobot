import sqlite3
import matplotlib.pyplot as plt
import datetime


def create_database():
    # Connecting to the database
    connection = sqlite3.connect('meetings.db')

    # Creating a table if not exists

    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS meetings (
        meet_id INTEGER,
        admin_id TEXT,
        date TEXT,
        duration INTEGER,
        description TEXT
        )
        '''
    )
    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
        user_id TEXT, meet_id INTEGER
        )
        '''
    )
    # Close the database connection
    connection.commit()
    connection.close()


def delete_database(connection):
    c = connection.cursor()
    c.execute('DROP TABLE IF EXISTS meetings')
    c.execute('DROP TABLE IF EXISTS users')


def print_all_data(connection):
    # Select all
    cursor = connection.execute("SELECT * FROM meetings")
    for row in cursor:
        print(row)


def insert_meeting(connection, meeting_id, admin_id, date, duration, description):
    # Insert meeting data
    connection.execute("INSERT INTO meetings (meet_id, admin_id, date, duration, description) VALUES (?, ?, ?, ?, ?)",
                       (meeting_id, admin_id, date, duration, description))
    connection.commit()
    connection.close()


def insert_users(connection, meet_id, users):
    for user in users:
        connection.execute("INSERT INTO users (user_id, meet_id) VALUES (?, ?)", (user, meet_id))
    connection.commit()


def plot_meeting_duration_distribution(connection):
    connection.execute('SELECT duration FROM meetings')
    meeting_durations = [row[0] for row in connection.fetchall()]

    plt.hist(meeting_durations, bins=10, alpha=0.7, color='b')
    plt.xlabel('Продолжительность встречи (минуты)')
    plt.ylabel('Частота')
    plt.title('Распределение продолжительности встреч')
    plt.show()


def plot_meeting_date_distribution(connection):
    connection.execute('SELECT date FROM meetings')
    meeting_dates = [row[0] for row in connection.fetchall()]

    plt.hist(meeting_dates, bins=30, alpha=0.7, color='g')
    plt.xlabel('Дата встречи')
    plt.ylabel('Частота')
    plt.title('Распределение встреч по датам')
    plt.show()


def plot_user_diagram(connection, user):

    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

    connection.execute('''
    SELECT date, duration
    FROM meetings 
    JOIN users 
    ON meetings.id = users.meet_id 
    WHERE users.user_id = ? AND meetings.date>=?
    ''', (user, week_ago))

    user_meetings = connection.fetchall()

    date_counts = {}
    for date, duration in user_meetings:
        date_str = date.strftime('%Y-%m-%d')
        if date_str in date_counts:
            date_counts[date_str] += duration
        else:
            date_counts[date_str] = duration

    plt.bar(date_counts.keys(), date_counts.values())
    plt.xlabel('Дата')
    plt.ylabel('Продолжительность встреч (минуты)')
    plt.title(f'Загруженность {user} за последнюю неделю')
    plt.show()


if __name__ == "__main__":
    # Connect to db
    connection = sqlite3.connect('meetings.db')
    # delete_database(connection)
    create_database()
    connection.commit()

    # insert_meeting(connection, 1, 'first', '2023-11-11', 60, 'Первая встреча')
    # insert_users(connection, 1, ['first', 'second', 'third'])
    # connection.commit()
    # print_all_data()
    connection.close()
