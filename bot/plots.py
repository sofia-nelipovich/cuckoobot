import db_interaction

import matplotlib.pyplot as plt
import datetime


def plot_meeting_duration_distribution(db):
    connection = db.get_connection()
    connection.execute('SELECT duration FROM meetings')
    meeting_durations = [row[0] for row in connection.fetchall()]

    plt.hist(meeting_durations, bins=10, alpha=0.7, color='b')
    plt.xlabel('Продолжительность встречи (минуты)')
    plt.ylabel('Частота')
    plt.title('Распределение продолжительности встреч')
    plt.show()


def plot_meeting_date_distribution(db):
    connection = db.get_connection()
    connection.execute('SELECT date FROM meetings')
    meeting_dates = [row[0] for row in connection.fetchall()]

    plt.hist(meeting_dates, bins=30, alpha=0.7, color='g')
    plt.xlabel('Дата встречи')
    plt.ylabel('Частота')
    plt.title('Распределение встреч по датам')
    plt.show()


def plot_user_diagram(db, user):
    connection = db.get_connection()

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
