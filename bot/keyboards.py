from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_menu_markup = InlineKeyboardMarkup(row_width=1)
start_menu_markup.add(
    InlineKeyboardButton(text="Войти", callback_data="login"),
)

main_menu_markup = InlineKeyboardMarkup(row_width=1)
main_menu_markup.add(
    InlineKeyboardButton(text="Мой календарь", callback_data="my_calendar"),
    InlineKeyboardButton(
        text="Добавить групповое событие", callback_data="add_group_event"
    ),
    InlineKeyboardButton(
        text="Добавить групповое событие на свободное время",
        callback_data="add_auto_group_event",
    ),
    InlineKeyboardButton(
        text="Статистика встреч по количеству",
        callback_data="get_plot_date",
    ),
    InlineKeyboardButton(
        text="Статистика по продолжительности",
        callback_data="get_plot_duration",
    ),
)

admin_main_menu_markup = InlineKeyboardMarkup(row_width=1)
admin_main_menu_markup.add(
    InlineKeyboardButton(text="Мой календарь", callback_data="my_calendar"),
    InlineKeyboardButton(
        text="Добавить групповое событие", callback_data="add_group_event"
    ),
    InlineKeyboardButton(
        text="Добавить групповое событие на свободное время",
        callback_data="add_auto_group_event",
    ),
    InlineKeyboardButton("Добавить участника", callback_data="add_member"),
    InlineKeyboardButton("Удалить участника", callback_data="remove_member"),
    InlineKeyboardButton(
        text="Статистика встреч по количеству",
        callback_data="get_plot_date",
    ),
    InlineKeyboardButton(
        text="Статистика по продолжительности",
        callback_data="get_plot_duration",
    ),
)

back_main_markup = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Назад", callback_data="back_to_main_menu")
)

back_to_calendar_markup = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Назад", callback_data="my_calendar")
)


def event_link_markup(event_link):
    markup = InlineKeyboardMarkup(row_width=1)
    if event_link and event_link.startswith(
        "http"
    ):  # Проверяем, что ссылка действительна
        markup.add(InlineKeyboardButton("Открыть событие в календаре", url=event_link))
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_main_menu"))
    return markup


def event_navigation_markup(curr_idx, total_events_count):
    event_menu_markup = InlineKeyboardMarkup()

    buttons = []

    if curr_idx > 0:
        buttons.append(
            InlineKeyboardButton(text="←", callback_data=f"prev_event:{curr_idx}")
        )
    if curr_idx < total_events_count - 1:
        buttons.append(
            InlineKeyboardButton(text="→", callback_data=f"next_event:{curr_idx}")
        )

    event_menu_markup.row(*buttons)

    event_menu_markup.row(
        InlineKeyboardButton(
            text="Редактировать", callback_data=f"edit_event:{curr_idx}"
        )
    )
    event_menu_markup.row(
        InlineKeyboardButton("Назад", callback_data="back_to_main_menu")
    )

    return event_menu_markup


def edit_event_markup(calendar_event_id, is_group):
    edit_event_markup = InlineKeyboardMarkup(row_width=1)
    if is_group:
        edit_event_markup.add(
            InlineKeyboardButton(
                text="Описание", callback_data=f"edit_description:{calendar_event_id}"
            ),
            InlineKeyboardButton(text="Назад", callback_data="my_calendar"),
        )
    else:
        edit_event_markup.add(
            InlineKeyboardButton(
                text="Имя", callback_data=f"edit_name:{calendar_event_id}"
            ),
            InlineKeyboardButton(
                text="Дата", callback_data=f"edit_date:{calendar_event_id}"
            ),
            InlineKeyboardButton(
                text="Время начала", callback_data=f"edit_start:{calendar_event_id}"
            ),
            InlineKeyboardButton(
                text="Продолжительность",
                callback_data=f"edit_duration:{calendar_event_id}",
            ),
            InlineKeyboardButton(
                text="Описание", callback_data=f"edit_description:{calendar_event_id}"
            ),
            InlineKeyboardButton(
                text="Удалить", callback_data=f"delete_event:{calendar_event_id}"
            ),
            InlineKeyboardButton(text="Назад", callback_data="my_calendar"),
        )
    return edit_event_markup


def group_edit_event_markup(calendar_event_id):
    group_edit_event_markup = InlineKeyboardMarkup(row_width=1)
    group_edit_event_markup.add(
        InlineKeyboardButton(
            text="Имя", callback_data=f"group_edit_name:{calendar_event_id}"
        ),
        InlineKeyboardButton(
            text="Дата", callback_data=f"group_edit_date:{calendar_event_id}"
        ),
        InlineKeyboardButton(
            text="Время начала", callback_data=f"group_edit_start:{calendar_event_id}"
        ),
        InlineKeyboardButton(
            text="Продолжительность",
            callback_data=f"group_edit_duration:{calendar_event_id}",
        ),
        InlineKeyboardButton(
            text="Описание", callback_data=f"group_edit_description:{calendar_event_id}"
        ),
        InlineKeyboardButton(
            text="Удалить", callback_data=f"group_delete_event:{calendar_event_id}"
        ),
        InlineKeyboardButton(text="Назад", callback_data="my_calendar"),
    )
    return group_edit_event_markup


def get_main_menu_keyboard_final():
    main_menu_markup = InlineKeyboardMarkup(row_width=1)
    main_menu_markup.add(
        InlineKeyboardButton("Создать группу", callback_data="create_group"),
    )
    return main_menu_markup
