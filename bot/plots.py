import db_interaction

import matplotlib.pyplot as plt
import datetime

def plot_meeting_duration_distribution(db):
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT duration FROM meetings')
    meeting_durations = [row[0] for row in cursor.fetchall()]

    plt.hist(meeting_durations, bins=10, alpha=0.7, color='b')
    plt.xlabel('Продолжительность встречи (минуты)')
    plt.ylabel('Частота')
    plt.title('Распределение продолжительности встреч')
    plt.show()


def plot_meeting_date_distribution(db):
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT date FROM meetings')
    meeting_dates = [datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%d.%m') for row in cursor.fetchall()]

    plt.hist(meeting_dates, bins=30, alpha=0.7, color='b')
    plt.xlabel('Дата встречи')
    plt.ylabel('Частота')
    plt.title('Распределение встреч по датам')
    plt.show()


def plot_user_diagram(db, user):
    connection = db.get_connection()

    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

    cursor = connection.cursor()

    cursor.execute('''
    SELECT date, duration
    FROM meetings 
    JOIN users 
    ON meetings.meet_id = users.meet_id 
    WHERE users.user_id = ?
    ''', (user, ))

    user_meetings = cursor.fetchall()
    date_counts = {}
    for day in range(7):
        new_day = (week_ago + datetime.timedelta(days=day)).strftime('%d.%m')
        date_counts[new_day] = 0

    for date, duration in user_meetings:
        dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        if dt >= week_ago:
            date_counts[dt.strftime('%d.%m')] = duration

    plt.bar(date_counts.keys(), date_counts.values())
    plt.xlabel('Дата')
    plt.ylabel('Продолжительность встреч (минуты)')
    plt.title(f'Загруженность {user} за последнюю неделю')
    plt.figure(figsize=(20, 6))
    plt.show()
