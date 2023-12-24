import db_interaction
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import pandas as pd


def get_last_week_dictionary():
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    dates = {}
    for day in range(0, 8):
        new_day = (week_ago + datetime.timedelta(days=day)).strftime('%d.%m')
        dates[new_day] = 0
    return week_ago, dates


def get_datetime_format(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')


def plot_meeting_duration_distribution(db, group_id):
    week_ago, date_counts = get_last_week_dictionary()

    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT date, SUM(duration)
                   FROM meetings
                   WHERE group_id = ? AND date >= ?
                   GROUP BY date
                   ''', (group_id, week_ago))
    meeting_durations = cursor.fetchall()
    for date, summ in meeting_durations:
        dt = get_datetime_format(date)
        date_counts[dt.strftime('%d.%m')] = summ

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())
    ax.set(xlabel='Дата', ylabel='Суммарное время встреч(минуты)', title='Распределение времени встреч по датам')


def plot_meeting_date_distribution(db, group_id):
    week_ago, date_counts = get_last_week_dictionary()

    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('''SELECT date, COUNT(*) 
                   FROM meetings
                   WHERE group_id = ? AND date >= ?
                   GROUP BY date
                   ''', (group_id, week_ago))
    dates = cursor.fetchall()

    for date, count in dates:
        dt = get_datetime_format(date)
        date_counts[dt.strftime('%d.%m')] = count

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())
    ax.set(xlabel='Дата', ylabel='Количество встреч', title='Распределение встреч по датам')


def plot_user_stats(db, user):
    week_ago, date_counts = get_last_week_dictionary()

    connection = db.get_connection()
    cursor = connection.cursor()

    cursor.execute('''
        SELECT date, duration
        FROM meetings 
        JOIN users 
        ON meetings.group_id = users.group_id 
        WHERE users.user_id = ? and meetings.date >= ?
    ''', (user, week_ago))

    user_meetings = cursor.fetchall()

    for date, duration in user_meetings:
        dt = get_datetime_format(date)
        date_counts[dt.strftime('%d.%m')] = duration

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())

    ax.set(xlabel='Дата', ylabel='Продолжительность встреч (минуты)', title=f'Загруженность {user} за последнюю неделю')


def plot_group_stats(db, group_id):
    week_ago, date_counts = get_last_week_dictionary()

    connection = db.get_connection()
    cursor = connection.cursor()

    cursor.execute('''
    SELECT date, duration
    FROM meetings 
    WHERE meetings.date >= ? AND group_id = ?
    ''', (week_ago, group_id))

    user_meetings = cursor.fetchall()
    for row in user_meetings:
        print(row)

    for row in date_counts:
        print(row)

    for date, duration in user_meetings:
        dt = get_datetime_format(date)
        date_counts[dt.strftime('%d.%m')] += duration

    ax = sns.barplot(x=date_counts.keys(), y=date_counts.values())

    ax.set(xlabel='Дата', ylabel='Продолжительность встреч (минуты)', title=f'Загруженность за последнюю неделю')


def funfact_user(db, user_id):
    connection = db.get_connection()
    cursor = connection.cursor()

    week_ago, date_counts = get_last_week_dictionary()

    cursor.execute('''
    SELECT duration
    FROM meetings 
    JOIN users 
    ON meetings.group_id = users.group_id 
    WHERE users.user_id = ? AND meetings.date >= ?
    ''', (user_id, week_ago))

    meetings_times = [row[0] for row in cursor.fetchall()]

    minutes = sum(meetings_times)
    hours = minutes // 60

    return f'Фанфакт: за последнюю неделю {user_id} провел(а) {hours}ч{minutes - hours * 60}м на встречах!\nСамая длинная встреча длилась {max(meetings_times)} минут!'


def funfact_group(db, group_id):
    connection = db.get_connection()
    cursor = connection.cursor()

    week_ago, date_counts = get_last_week_dictionary()

    cursor.execute('''
    SELECT duration
    FROM meetings
    WHERE date >= ? AND group_id = ?
    ''', (week_ago, group_id))

    meetings_times = [row[0] for row in cursor.fetchall()]

    minutes = sum(meetings_times)
    hours = minutes // 60

    return f'Фанфакт: за последнюю неделю вы провели {hours}ч{minutes - hours * 60}м на встречах!\nСамая длинная встреча длилась {max(meetings_times)} минут!'


def funfact_popular_time(db, group_id):
    connection = db.get_connection()
    cursor = connection.cursor()

    cursor.execute(
        '''
        SELECT meet_id, date 
        FROM meetings
        WHERE group_id = ?
        ''', (group_id,)
    )
    meetings = cursor.fetchall()
    connection.close()

    times = [0 for _ in range(24)]
    days_of_week = [0 for _ in range(7)]

    popular_day_count = 0
    popular_hour_count = 0
    popular_day_ind = 0
    popular_hour_ind = 0

    for meet, date in meetings:
        day_of_week = get_datetime_format(date).weekday()
        hour = get_datetime_format(date).hour

        days_of_week[day_of_week] += 1
        times[hour] += 1

        if days_of_week[day_of_week] > popular_day_count:
            popular_day_count = days_of_week[day_of_week]
            popular_day_ind = day_of_week
        if times[hour] > popular_hour_count:
            popular_hour_count = times[hour]
            popular_hour_ind = hour

    days_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'восресенье']

    return f'Фанфакт: самый популярный день недели для встреч в вашей группе - {days_names[popular_day_ind]}, а самое популярное время - {popular_hour_ind} часов!\n'



