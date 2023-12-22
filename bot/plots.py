import db_interaction

import seaborn as sns

import matplotlib.pyplot as plt
import datetime


def get_last_week_dictionary():
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    dates = {}
    for day in range(7):
        new_day = (week_ago + datetime.timedelta(days=day)).strftime('%d.%m')
        dates[new_day] = 0
    return week_ago, dates


def get_datetime_format(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')


def plot_meeting_duration_distribution(db):
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT date, SUM(duration)
                   FROM meetings
                   GROUP BY date
                   ''')
    week_ago, date_counts = get_last_week_dictionary()
    meeting_durations = cursor.fetchall()
    for date, summ in meeting_durations:
        dt = get_datetime_format(date)
        if dt >= week_ago:
            date_counts[dt.strftime('%d.%m')] = summ

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())
    ax.set(xlabel='Дата', ylabel='Суммарное время встреч(минуты)', title='Распределение времени встреч по датам')


def plot_meeting_date_distribution(db):
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT date, COUNT(*) 
                   FROM meetings
                   GROUP BY date
                   ''')
    dates = cursor.fetchall()

    week_ago, date_counts = get_last_week_dictionary()

    for date, count in dates:
        dt = get_datetime_format(date)
        if dt >= week_ago:
            date_counts[dt.strftime('%d.%m')] = count

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())
    ax.set(xlabel='Дата', ylabel='Количество встреч', title='Распределение встреч по датам')


def plot_user_diagram(db, user):
    connection = db.get_connection()
    cursor = connection.cursor()

    cursor.execute('''
    SELECT date, duration
    FROM meetings 
    JOIN users 
    ON meetings.meet_id = users.meet_id 
    WHERE users.user_id = ?
    ''', (user,))

    user_meetings = cursor.fetchall()
    week_ago, date_counts = get_last_week_dictionary()

    for date, duration in user_meetings:
        dt = get_datetime_format(date)
        if dt >= week_ago:
            date_counts[dt.strftime('%d.%m')] = duration

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())

    ax.set(xlabel='Дата', ylabel='Продолжительность встреч (минуты)', title=f'Загруженность {user} за последнюю неделю')
