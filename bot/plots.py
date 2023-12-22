import db_interaction
import seaborn as sns
import matplotlib.pyplot as plt
import datetime


def get_last_week_dictionary():
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    dates = {}
    for day in range(1, 8):
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
    ON meetings.meet_id = users.meet_id 
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
    ON meetings.meet_id = users.meet_id 
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
