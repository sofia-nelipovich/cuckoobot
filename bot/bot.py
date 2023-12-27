from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
)
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from googleapiclient.errors import HttpError
from aiogram.utils.exceptions import MessageNotModified
from datetime import datetime, timedelta
import re
import random

from config import BOT_TOKEN
import google_calendar as google_calendar
import keyboards as kb
import db_interaction as pg
from states import (
    LoginFrom,
    CreateEvent,
    EditEventState,
    EditGroupEventState,
    CreateGroupEvent,
    GroupCreation,
    GroupAdmin,
)
import db


bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = db.Database("db.db")


@dp.callback_query_handler(lambda c: c.data == "create_group")
async def create_group_command(callback_query: types.CallbackQuery):
    await GroupCreation.waiting_for_group_name.set()
    await bot.send_message(
        callback_query.from_user.id, "🏷 Введите название для вашей новой группы:"
    )


@dp.message_handler(state=GroupCreation.waiting_for_group_name)
async def group_name_entered(message: types.Message, state: FSMContext):
    group_name = message.text
    admin_id = message.from_user.id
    group_id, group_code = db.create_group(group_name, admin_id)
    db.update_user_group(admin_id, group_id)
    # Создание ссылки для присоединения к группе
    join_link = f"https://t.me/realcuckoo_bot?start={group_code}"
    await state.finish()
    await message.answer(
        f"✅ Группа '{group_name}' успешно создана! Вот ваша пригласительная ссылка: {join_link}",
        reply_markup=kb.back_main_markup,
    )


@dp.callback_query_handler(lambda c: c.data == "get_plot_date")
async def get_plot_date(callback_query: CallbackQuery):
    uid = callback_query.from_user.id
    group_id = db.get_current_group_id(uid)

    plot_buffer = pg.plot_meeting_date_distribution(db, group_id)

    await bot.send_photo(
        chat_id=uid,
        photo=plot_buffer,
    )

    plot_buffer.close()

    fun_fact_text = pg.get_random_fun_fact(
        db, uid, group_id, callback_query.from_user.full_name
    )

    await bot.send_message(
        chat_id=uid, text=fun_fact_text, reply_markup=kb.back_main_markup
    )


@dp.callback_query_handler(lambda c: c.data == "get_plot_duration")
async def get_plot_duration(callback_query: CallbackQuery):
    uid = callback_query.from_user.id
    group_id = db.get_current_group_id(uid)

    plot_buffer = pg.plot_meeting_duration_distribution(db, group_id)

    await bot.send_photo(
        chat_id=uid,
        photo=plot_buffer,
    )

    plot_buffer.close()

    fun_fact_text = pg.get_random_fun_fact(
        db, uid, group_id, callback_query.from_user.full_name
    )

    await bot.send_message(
        chat_id=uid, text=fun_fact_text, reply_markup=kb.back_main_markup
    )


@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    user_id = message.from_user.id

    if args:
        if db.check_group_exists(args):
            calendar_id = db.get_calendar_id(user_id)
            group_code = args
            group_id = db.get_group_id(group_code)

            # Проверка, состоит ли пользователь уже в группе
            current_group_id = db.get_current_group_id(user_id)
            if current_group_id and current_group_id == group_id[0]:
                await message.answer(
                    "Вы уже являетесь участником этой группы.",
                    reply_markup=kb.main_menu_markup,
                )
            else:
                db.update_user_group(user_id, group_id[0])
                if calendar_id:
                    await message.answer(
                        "👋 Добро пожаловать в бота!",
                        reply_markup=kb.main_menu_markup,
                    )
                else:
                    group_code = args
                    db.join_group(user_id, group_code)
                    await message.answer(
                        "🌟 Чтобы начать, пожалуйста, разрешите доступ боту к вашему календарю Google. Это необходимо для управления вашими событиями.\n\n"
                        "🔍 Подробная инструкция по настройке доступа представлена здесь: <a href='https://telegra.ph/Kak-otkryt-dostup-k-kalendaryu-12-24'>Как открыть доступ к календарю</a>\n\n"
                        "📧 После настройки доступа нажмите 'Войти'.",
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb.start_menu_markup,
                    )

                members = db.get_group_members(group_code)
                for member_id in members:
                    if member_id != user_id:
                        await bot.send_message(
                            member_id,
                            f"К группе присоединился новый участник : {message.from_user.full_name}",
                        )
        else:
            await message.answer("Группа с таким кодом не найдена.")

    else:
        # Обработка стандартной команды /start без идентификатора группы
        calendar_id = db.get_calendar_id(user_id)
        if calendar_id:
            if db.is_user_in_group(user_id):
                if db.check_if_user_is_group_admin(user_id):
                    await message.answer(
                        "👋 Добро пожаловать в бота!",
                        reply_markup=kb.admin_main_menu_markup,
                    )
                else:
                    await message.answer(
                        "👋 Добро пожаловать в бота!",
                        reply_markup=kb.main_menu_markup,
                    )
            else:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text="👋 Добро пожаловать в бота! Теперь вы можете создать новую группу или присоединиться к существующей по пригласительной ссылке.",
                    reply_markup=kb.get_main_menu_keyboard_final(),
                )
        else:
            await message.answer(
                "🌟 Чтобы начать, пожалуйста, разрешите доступ боту к вашему календарю Google. Это необходимо для управления вашими событиями.\n\n"
                "🔍 Подробная инструкция по настройке доступа представлена здесь: <a href='https://telegra.ph/Kak-otkryt-dostup-k-kalendaryu-12-24'>Как открыть доступ к календарю</a>\n\n"
                "📧 После настройки доступа нажмите 'Войти'.",
                parse_mode=ParseMode.HTML,
                reply_markup=kb.start_menu_markup,
            )


@dp.callback_query_handler(lambda c: c.data == "login")
async def login(callback_query: CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Пожалуйста, введите идентификатор вашего календаря Google:",
    )
    await LoginFrom.waiting_for_calendar_id.set()


@dp.message_handler(state=LoginFrom.waiting_for_calendar_id)
async def calendar_id_received(message: Message, state: FSMContext):
    if "@gmail.com" in message.text or "@group.calendar.google.com" in message.text:
        try:
            google_calendar.add_calendar(calendar_id=message.text)
            await bot.send_message(
                chat_id=message.from_user.id,
                text="Идентификатор вашего календаря успешно добавлен!",
            )
            user_id = message.from_user.id
            calendar_id = message.text

            await state.finish()
            group_id = db.get_user_group_id(user_id)
            if group_id:
                db.update_user_calendar_id(user_id, calendar_id)
                await message.answer(
                    "👋 Добро пожаловать в бота!",
                    reply_markup=kb.main_menu_markup,
                )
            else:
                db.insert_user(user_id=user_id, calendar_id=calendar_id, group_id="")
                if db.check_if_user_is_group_admin(user_id):
                    await bot.send_message(
                        chat_id=message.from_user.id,
                        text="👋 Добро пожаловать в бота!",
                        reply_markup=kb.admin_main_menu_markup,
                    )
                else:
                    await bot.send_message(
                        chat_id=message.from_user.id,
                        text="👋 Добро пожаловать в бота! Теперь вы можете создать новую группу или присоединиться к существующей по пригласительной ссылке.",
                        reply_markup=kb.get_main_menu_keyboard_final(),
                    )
        except HttpError as e:
            await bot.send_message(
                chat_id=message.from_user.id,
                text="К сожалению, произошла ошибка при доступе к вашему календарю. Пожалуйста, убедитесь, что боту предоставлены соответствующие права доступа, и попробуйте снова.",
            )
    else:
        await message.reply(
            "📌 Для продолжения, введите идентификатор вашего календаря Google. Идентификатор обычно имеет формат почты Gmail или специфический формат группового календаря Google.\n"
            "🔹 Пример для личного календаря: ваш_email@gmail.com\n"
            "🔹 Пример для группового календаря: ваш_идентификатор@group.calendar.google.com\n"
            "✏️ Введите идентификатор календаря ниже и нажмите отправить."
        )


@dp.callback_query_handler(lambda c: c.data == "my_calendar")
async def get_calendar(callback_query: CallbackQuery):
    uid = callback_query.from_user.id
    calendar_id = db.get_calendar_id(uid)

    try:
        events_dict = google_calendar.get_events_for_24(calendar_id)
        events = list(events_dict.values())

        if not events:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text="Сегодня нет никаких планов!",
                reply_markup=kb.back_main_markup,
            )
        else:
            try:
                await bot.edit_message_text(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    text=events[0],
                    reply_markup=kb.event_navigation_markup(0, len(events)),
                )
            except MessageNotModified:
                pass
    except HttpError as e:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="К сожалению, произошла ошибка при доступе к вашему календарю. Пожалуйста, убедитесь, что боту предоставлены соответствующие права доступа, и попробуйте снова.",
            reply_markup=kb.back_main_markup,
        )


@dp.callback_query_handler(lambda c: "prev_event" in c.data or "next_event" in c.data)
async def navigate_events(callback_query: CallbackQuery):
    uid = callback_query.from_user.id
    calendar_id = db.get_calendar_id(uid)
    events_dict = google_calendar.get_events_for_24(calendar_id)
    events = list(events_dict.values())

    curr_idx = int(callback_query.data.split(":")[1])
    next_idx = curr_idx

    if "prev_event" in callback_query.data and curr_idx > 0:
        next_idx -= 1
    elif "next_event" in callback_query.data and curr_idx < len(events) - 1:
        next_idx += 1

    try:
        if next_idx != curr_idx:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=events[next_idx],
                reply_markup=kb.event_navigation_markup(next_idx, len(events)),
            )
    except MessageNotModified:
        pass


@dp.callback_query_handler(lambda c: "edit_event" in c.data)
async def edit_event(callback_query: CallbackQuery):
    event_idx = int(callback_query.data.split(":")[1])

    uid = callback_query.from_user.id
    calendar_id = db.get_calendar_id(uid)
    events_dict = google_calendar.get_events_for_24(calendar_id)
    event_ids = list(events_dict.keys())
    events = list(events_dict.values())

    calendar_event_id = event_ids[event_idx]

    #  if events[0] is group event
    admin_id = db.check_is_group_event(calendar_event_id)
    if admin_id:
        if uid == admin_id:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=events[event_idx],
                reply_markup=kb.group_edit_event_markup(calendar_event_id),
            )
        else:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=events[event_idx],
                reply_markup=kb.edit_event_markup(calendar_event_id, True),
            )
    else:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=events[event_idx],
            reply_markup=kb.edit_event_markup(calendar_event_id, False),
        )


@dp.callback_query_handler(lambda c: c.data.startswith("edit_name"))
async def callback_edit_name(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditEventState.waiting_for_new_name.set()
    await bot.send_message(
        callback_query.from_user.id, "Пожалуйста, введите название для нового события:"
    )


@dp.message_handler(state=EditEventState.waiting_for_new_name)
async def process_new_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data["calendar_event_id"]
    uid = message.from_user.id
    calendar_id = db.get_calendar_id(uid)

    event_link = google_calendar.update_event_name(calendar_id, event_id, message.text)

    await state.finish()
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Название события обновлено.",
        reply_markup=kb.event_link_markup(event_link),
    )


@dp.callback_query_handler(lambda c: c.data.startswith("group_edit_name"))
async def callback_group_edit_name(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditGroupEventState.waiting_for_new_name.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новое название события:"
    )


# Изменение встреч
@dp.message_handler(state=EditGroupEventState.waiting_for_new_name)
async def process_group_new_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data["calendar_event_id"]
    user_id = message.from_user.id

    event_calendar_ids_with_google_ids = db.get_group_event(event_id)

    user_event_links = {}

    for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
        event_link = google_calendar.update_event_name(
            calendar_id, calendar_event_id, message.text
        )
        member_user_id = db.get_user_id_by_calendar_id(calendar_id)
        print(member_user_id)
        if member_user_id:
            user_event_links[member_user_id] = event_link

    await state.finish()
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Название события обновлено.",
        reply_markup=kb.event_link_markup(
            user_event_links.get(user_id, "Ссылка не найдена")
        ),
    )

    members = db.get_group_members_by_user_id(user_id)
    for member_id in members:
        if member_id != user_id:
            event_link = user_event_links.get(member_id)
            print(event_link)
            event_link_markup = kb.event_link_markup(event_link)
            await bot.send_message(
                member_id,
                f"Админ изменил название групповой встречи",
                reply_markup=event_link_markup,
            )


@dp.callback_query_handler(lambda c: c.data.startswith("edit_date"))
async def callback_edit_date(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditEventState.waiting_for_new_date.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новую дату(ДД-ММ-ГГГГ):"
    )


@dp.message_handler(state=EditEventState.waiting_for_new_date)
async def process_new_date(message: types.Message, state: FSMContext):
    try:
        new_parsed_date = datetime.strptime(message.text, "%d-%m-%Y")
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        uid = message.from_user.id
        calendar_id = db.get_calendar_id(uid)
        event_link = google_calendar.update_event_date(
            calendar_id, event_id, new_parsed_date
        )
        await state.finish()
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Дата события обновлена.",
            reply_markup=kb.event_link_markup(event_link),
        )
    except ValueError:
        await message.reply(
            "Формат даты неверен. Введите дату в следующем формате ДД-ММ-ГГГГ (например, 01-01-2023):"
        )


@dp.callback_query_handler(lambda c: c.data.startswith("group_edit_date"))
async def callback_group_edit_date(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditGroupEventState.waiting_for_new_date.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новую дату(ДД-ММ-ГГГГ):"
    )


@dp.message_handler(state=EditGroupEventState.waiting_for_new_date)
async def process_group_new_date(message: types.Message, state: FSMContext):
    try:
        new_parsed_date = datetime.strptime(message.text, "%d-%m-%Y")
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        user_id = message.from_user.id

        event_calendar_ids_with_google_ids = db.get_group_event(event_id)
        user_event_links = {}

        for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
            event_link = google_calendar.update_event_date(
                calendar_id, calendar_event_id, new_parsed_date
            )
            member_user_id = db.get_user_id_by_calendar_id(calendar_id)
            if member_user_id:
                user_event_links[member_user_id] = event_link

        await state.finish()
        await bot.send_message(
            chat_id=user_id,
            text="Дата события обновлена.",
            reply_markup=kb.event_link_markup(user_event_links.get(user_id)),
        )

        members = db.get_group_members_by_user_id(user_id)
        for member_id in members:
            if member_id != user_id:
                event_link = user_event_links.get(member_id)
                if event_link and event_link.startswith("http"):
                    event_link_markup = InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Ссылка на событие", url=event_link)
                    )
                else:
                    event_link_markup = None

                await bot.send_message(
                    member_id,
                    f"Админ изменил дату группового события: {message.text}",
                    reply_markup=event_link_markup,
                )
    except ValueError:
        await message.reply("Пожалуйста, введите дату в формате ДД-ММ-ГГГГ:")


@dp.callback_query_handler(lambda c: c.data.startswith("edit_start"))
async def callback_edit_start(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditEventState.waiting_for_new_start.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новую время начала(ЧЧ:MM):"
    )


@dp.message_handler(state=EditEventState.waiting_for_new_start)
async def process_new_start(message: types.Message, state: FSMContext):
    time_re = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$")
    if time_re.match(message.text):
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        uid = message.from_user.id
        calendar_id = db.get_calendar_id(uid)
        event_link = google_calendar.update_event_start(
            calendar_id, event_id, message.text
        )
        await state.finish()
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Время начала события обновлено.",
            reply_markup=kb.event_link_markup(event_link),
        )
    else:
        await message.reply("Пожалуйста, введите время в формате ЧЧ:ММ")


@dp.callback_query_handler(lambda c: c.data.startswith("group_edit_start"))
async def callback_edit_start(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditGroupEventState.waiting_for_new_start.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новую время начала(ЧЧ:MM):"
    )


@dp.message_handler(state=EditGroupEventState.waiting_for_new_start)
async def process_group_new_start(message: types.Message, state: FSMContext):
    time_re = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$")
    if time_re.match(message.text):
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        user_id = message.from_user.id

        event_calendar_ids_with_google_ids = db.get_group_event(event_id)
        user_event_links = {}

        for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
            event_link = google_calendar.update_event_start(
                calendar_id, calendar_event_id, message.text
            )
            member_user_id = db.get_user_id_by_calendar_id(calendar_id)
            if member_user_id:
                user_event_links[member_user_id] = event_link

        await state.finish()
        await bot.send_message(
            chat_id=user_id,
            text="Время начала события обновлено.",
            reply_markup=kb.event_link_markup(user_event_links.get(user_id)),
        )

        members = db.get_group_members_by_user_id(user_id)
        for member_id in members:
            if member_id != user_id:
                event_link_markup = None
                if member_id in user_event_links and user_event_links[
                    member_id
                ].startswith("http"):
                    event_link_markup = InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            "Ссылка на событие", url=user_event_links[member_id]
                        )
                    )

                await bot.send_message(
                    member_id,
                    f"Админ изменил время начала группового события: {message.text}",
                    reply_markup=event_link_markup,
                )
    else:
        await message.reply("Пожалуйста, введите время в формате ЧЧ:ММ")


@dp.callback_query_handler(lambda c: c.data.startswith("edit_duration"))
async def callback_edit_duration(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditEventState.waiting_for_new_duration.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите продолжительность(в минутах):"
    )


@dp.message_handler(state=EditEventState.waiting_for_new_duration)
async def process_new_duration(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        uid = message.from_user.id
        calendar_id = db.get_calendar_id(uid)
        event_link = google_calendar.update_event_duration(
            calendar_id, event_id, int(message.text)
        )
        await state.finish()
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Продолжительность события обновлена.",
            reply_markup=kb.event_link_markup(event_link),
        )
    else:
        await bot.send_message(
            message.from_user.id,
            "Пожалуйста, введите продолжительность в минутах (число).",
        )


@dp.callback_query_handler(lambda c: c.data.startswith("group_edit_duration"))
async def callback_group_edit_duration(
    callback_query: CallbackQuery, state: FSMContext
):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditGroupEventState.waiting_for_new_duration.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите продолжительность(в минутах):"
    )


@dp.message_handler(state=EditGroupEventState.waiting_for_new_duration)
async def process_group_new_duration(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        user_data = await state.get_data()
        event_id = user_data["calendar_event_id"]
        user_id = message.from_user.id

        event_calendar_ids_with_google_ids = db.get_group_event(event_id)
        user_event_links = {}

        for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
            event_link = google_calendar.update_event_duration(
                calendar_id, calendar_event_id, int(message.text)
            )
            member_user_id = db.get_user_id_by_calendar_id(calendar_id)
            if member_user_id:
                user_event_links[member_user_id] = event_link

        await state.finish()
        await bot.send_message(
            chat_id=user_id,
            text="Продолжительность события обновлена.",
            reply_markup=kb.event_link_markup(user_event_links.get(user_id)),
        )

        members = db.get_group_members_by_user_id(user_id)
        for member_id in members:
            if member_id != user_id:
                event_link_markup = None
                if member_id in user_event_links and user_event_links[
                    member_id
                ].startswith("http"):
                    event_link_markup = InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            "Ссылка на событие", url=user_event_links[member_id]
                        )
                    )

                await bot.send_message(
                    member_id,
                    f"Админ изменил продолжительность группового события: {message.text} минут",
                    reply_markup=event_link_markup,
                )
    else:
        await bot.send_message(
            message.from_user.id,
            "Пожалуйста, введите продолжительность в минутах (число).",
        )


@dp.callback_query_handler(lambda c: c.data.startswith("edit_description"))
async def callback_edit_description(callback_query: CallbackQuery, state: FSMContext):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditEventState.waiting_for_new_description.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новое описание(- если нет):"
    )


@dp.message_handler(state=EditEventState.waiting_for_new_description)
async def process_new_description(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data["calendar_event_id"]
    uid = message.from_user.id
    calendar_id = db.get_calendar_id(uid)

    event_link = google_calendar.update_event_description(
        calendar_id, event_id, message.text
    )

    await state.finish()
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Описание события обновлено.",
        reply_markup=kb.event_link_markup(event_link),
    )


@dp.callback_query_handler(lambda c: c.data.startswith("group_edit_description"))
async def callback_group_edit_description(
    callback_query: CallbackQuery, state: FSMContext
):
    calendar_event_id = callback_query.data.split(":")[1]
    await state.update_data(calendar_event_id=calendar_event_id)

    await EditGroupEventState.waiting_for_new_description.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите новое описание(- если нет):"
    )


@dp.message_handler(state=EditGroupEventState.waiting_for_new_description)
async def process_group_new_description(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data["calendar_event_id"]
    user_id = message.from_user.id

    event_calendar_ids_with_google_ids = db.get_group_event(event_id)
    user_event_links = {}

    for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
        event_link = google_calendar.update_event_description(
            calendar_id, calendar_event_id, message.text
        )
        member_user_id = db.get_user_id_by_calendar_id(calendar_id)
        if member_user_id:
            user_event_links[member_user_id] = event_link

    await state.finish()
    await bot.send_message(
        chat_id=user_id,
        text="Описание события обновлено.",
        reply_markup=kb.event_link_markup(user_event_links.get(user_id)),
    )

    members = db.get_group_members_by_user_id(user_id)
    for member_id in members:
        if member_id != user_id:
            event_link_markup = None
            if member_id in user_event_links and user_event_links[member_id].startswith(
                "http"
            ):
                event_link_markup = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        "Ссылка на событие", url=user_event_links[member_id]
                    )
                )

            await bot.send_message(
                member_id,
                f"Админ изменил описание группового события: {message.text}",
                reply_markup=event_link_markup,
            )


@dp.callback_query_handler(lambda c: c.data.startswith("delete_event"))
async def callback_delete_event(callback_query: CallbackQuery):
    calendar_event_id = callback_query.data.split(":")[1]
    uid = callback_query.from_user.id
    calendar_id = db.get_calendar_id(uid)

    try:
        google_calendar.delete_event(calendar_id, calendar_event_id)
    except HttpError as error:
        print(f"Ошибка при удалении события: {error}")
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Произошла ошибка при удалении события.",
        )
    else:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Событие было успешно удалено из вашего календаря.",
        )

    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Добро пожаловать в бота. Выберите:",
        reply_markup=kb.main_menu_markup,
    )


@dp.callback_query_handler(lambda c: c.data.startswith("group_delete_event"))
async def callback_group_delete_event(callback_query: CallbackQuery):
    event_id = callback_query.data.split(":")[1]
    event_calendar_ids_with_google_ids = db.get_group_event(event_id)

    for calendar_event_id, calendar_id in event_calendar_ids_with_google_ids:
        try:
            google_calendar.delete_event(calendar_id, calendar_event_id)
        except HttpError as error:
            print(f"Ошибка при удалении события: {error}")
            continue

    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Событие удалено",
    )

    user_id = callback_query.from_user.id
    members = db.get_group_members_by_user_id(user_id)
    for member_id in members:
        if member_id != user_id:
            await bot.send_message(
                member_id,
                "Админ удалил групповое событие!",
            )

    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Добро пожаловать в бота. Выберите:",
        reply_markup=kb.main_menu_markup,
    )


@dp.callback_query_handler(lambda c: c.data == "back_to_main_menu")
async def back_to_menu(callback_query: CallbackQuery):
    if db.check_if_user_is_group_admin(callback_query.from_user.id):
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="👋 Добро пожаловать в бота!",
            reply_markup=kb.admin_main_menu_markup,
        )
    else:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="👋 Добро пожаловать в бота!",
            reply_markup=kb.main_menu_markup,
        )


@dp.callback_query_handler(lambda c: c.data == "back_to_main_menu", state="*")
async def back_to_menu(callback_query: CallbackQuery, state: FSMContext):
    await state.finish()
    if db.check_if_user_is_group_admin(callback_query.from_user.id):
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="👋 Добро пожаловать в бота!",
            reply_markup=kb.admin_main_menu_markup,
        )
    else:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="👋 Добро пожаловать в бота!",
            reply_markup=kb.main_menu_markup,
        )


@dp.callback_query_handler(lambda c: c.data == "add_group_event")
async def add_group_event(callback_query: CallbackQuery):
    await CreateEvent.waiting_for_title.set()
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите название события:",
        reply_markup=kb.back_main_markup,
    )


@dp.message_handler(state=CreateEvent.waiting_for_title)
async def process_group_event_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["title"] = message.text
    await CreateEvent.next()
    await bot.send_message(message.from_user.id, "Введите дату события (DD-MM-YYYY):")


@dp.message_handler(state=CreateEvent.waiting_for_date)
async def process_group_event_date(message: types.Message, state: FSMContext):
    try:
        parsed_date = datetime.strptime(message.text, "%d-%m-%Y")
        async with state.proxy() as data:
            data["date"] = parsed_date.strftime("%d-%m-%Y")
        await CreateEvent.next()
        await bot.send_message(message.from_user.id, "Введите время начала (ЧЧ:ММ)")
    except ValueError:
        await message.reply("Пожалуйста, введите дату в формате ДД-ММ-ГГГГ:")


@dp.message_handler(state=CreateEvent.waiting_for_start_time)
async def process_group_event_start_time(message: types.Message, state: FSMContext):
    time_re = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$")
    if time_re.match(message.text):
        async with state.proxy() as data:
            data["start_time"] = message.text
        await CreateEvent.next()
        await bot.send_message(
            message.from_user.id, "Введите продолжительность (в минутах):"
        )
    else:
        await message.reply("Пожалуйста, введите время в формате ЧЧ:ММ")


@dp.message_handler(state=CreateEvent.waiting_for_duration)
async def process_group_event_duration(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        async with state.proxy() as data:
            data["duration"] = int(message.text)

        await CreateEvent.next()
        await bot.send_message(message.from_user.id, "Введите описание(- если нет):")
    else:
        await bot.send_message(
            message.from_user.id,
            "Пожалуйста, введите продолжительность в минутах (число).",
        )


@dp.message_handler(state=CreateEvent.waiting_for_description)
async def process_group_event_creation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text
        uid = message.from_user.id
        group_id = db.get_user_group_id(uid)
        users = db.get_users_and_calendar_ids_in_same_group(uid)
        editing_message = await bot.send_message(chat_id=uid, text="Создаём событие...")

        user_event_links = {}

        try:
            meet_id = random.randint(100000, 999999)  # Секретный код для meet_id
            for user_id, calendar_id in users:
                calendar_event_id, event_link = google_calendar.insert_group_event(
                    calendar_id, data
                )
                user_event_links[user_id] = event_link
                if user_id == uid:
                    user_event_link = event_link

                start_time = datetime.strptime(
                    data["date"] + " " + data["start_time"], "%d-%m-%Y %H:%M"
                ).strftime("%Y-%m-%d %H:%M:%S")

                db.insert_calendar_event_id(meet_id, calendar_event_id, calendar_id)

            db.insert_group_meeting(
                meet_id,
                group_id,
                start_time,
                data["duration"],
                data["title"],
                data["description"],
            )

            await bot.edit_message_text(
                chat_id=uid,
                message_id=editing_message.message_id,
                text="Событие успешно добавлено в ваши календари.",
                reply_markup=kb.event_link_markup(user_event_link),
            )

            # Отправка уведомлений участникам группы
            members = db.get_group_members_by_user_id(uid)
            for member_id in members:
                if member_id != uid:
                    event_link_markup = None
                    if member_id in user_event_links and user_event_links[
                        member_id
                    ].startswith("http"):
                        event_link_markup = InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                "Ссылка на событие", url=user_event_links[member_id]
                            )
                        )

                    await bot.send_message(
                        member_id,
                        f"Создано новое групповое событие: {data['title']}",
                        reply_markup=event_link_markup,
                    )

        except HttpError as e:
            await bot.send_message(
                chat_id=uid,
                text="Произошла ошибка при добавлении события. Убедитесь, что боту предоставлен доступ на запись в ваши календари.",
                reply_markup=kb.back_main_markup,
            )

        await state.finish()


@dp.callback_query_handler(lambda c: c.data == "add_auto_group_event")
async def add_auto_group_event(callback_query: CallbackQuery):
    await CreateGroupEvent.waiting_for_title.set()
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите название события:",
        reply_markup=kb.back_main_markup,
    )


@dp.message_handler(state=CreateGroupEvent.waiting_for_title)
async def process_auto_group_event_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["title"] = message.text
    await CreateGroupEvent.next()
    await bot.send_message(message.from_user.id, "Введите длительность(в минутах):")


@dp.message_handler(state=CreateGroupEvent.waiting_for_duration)
async def process_auto_group_event_duration(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        async with state.proxy() as data:
            data["duration"] = int(message.text)

        await CreateGroupEvent.next()
        await bot.send_message(message.from_user.id, "Введите описание(- если нет):")
    else:
        await bot.send_message(
            message.from_user.id,
            "Пожалуйста, введите продолжительность в минутах (число).",
        )


@dp.message_handler(state=CreateGroupEvent.waiting_for_description)
async def process_auto_group_event_creation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text

        uid = message.from_user.id
        group_id = db.get_user_group_id(uid)
        searching_message = await bot.send_message(
            chat_id=message.from_user.id,
            text="Ищем ближайшее доступное время...",
        )

        duration = data["duration"]
        users = db.get_users_and_calendar_ids_in_same_group(uid)
        calendar_ids = [user[1] for user in users]

        available_slot = google_calendar.get_nearest_available_time_slot(
            calendar_ids, duration
        )

        user_event_link = None
        user_event_links = {}

        if available_slot:
            meet_id = random.randint(
                100000, 999999
            )  # Шестизначный секретный код для meet_id
            data["date_and_start_time"] = available_slot
            available_slot = (available_slot + timedelta(hours=3)).replace(tzinfo=None)

            for user_id, calendar_id in users:
                try:
                    (
                        calendar_event_id,
                        event_link,
                    ) = google_calendar.insert_auto_group_event(calendar_id, data)
                    user_event_links[user_id] = event_link
                    if user_id == uid:
                        user_event_link = event_link

                    db.insert_calendar_event_id(meet_id, calendar_event_id, calendar_id)
                except HttpError as error:
                    print(f"Ошибка при добавлении события: {error}")
                    continue

            db.insert_group_meeting(
                meet_id,
                group_id,
                available_slot,
                data["duration"],
                data["title"],
                data["description"],
            )

            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=searching_message.message_id,
                text="Событие успешно добавлено в ваши календари.",
                reply_markup=kb.event_link_markup(user_event_link),
            )

            members = db.get_group_members_by_user_id(uid)
            for member_id in members:
                if member_id != uid:
                    event_link_markup = None

                    if member_id in user_event_links and user_event_links[
                        member_id
                    ].startswith("http"):
                        event_link_markup = InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                "Ссылка на событие", url=user_event_links[member_id]
                            )
                        )

                    await bot.send_message(
                        member_id,
                        f"Создано новое групповое событие: {data['title']}",
                        reply_markup=event_link_markup,
                    )

        else:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=searching_message.message_id,
                text="К сожалению, не удалось найти доступное время в ближайшие 24 часа.",
                reply_markup=kb.back_main_markup,
            )

        await state.finish()


@dp.callback_query_handler(text="add_member")
async def add_member(callback_query: types.CallbackQuery):
    group_code = db.get_group_code(callback_query.from_user.id)
    if group_code:
        invite_link = f"https://t.me/realcuckoo_bot?start={group_code}"
        await callback_query.message.answer(
            f"Пригласительная ссылка: {invite_link}", reply_markup=kb.back_main_markup
        )
    else:
        await callback_query.message.answer(
            "Вы не являетесь админом", reply_markup=kb.back_main_markup
        )


@dp.callback_query_handler(text="remove_member")
async def start_remove_member(callback_query: types.CallbackQuery, state: FSMContext):
    admin_id = callback_query.from_user.id
    group_id = db.get_user_group_id(admin_id)
    member_emails = db.get_group_members_emails(group_id)
    email_list = "\n".join(member_emails)
    await callback_query.message.answer(
        f"Участники группы:\n{email_list}\nВведите почту участника для удаления:",
        reply_markup=kb.back_main_markup,
    )
    await GroupAdmin.RemoveMember.set()


@dp.message_handler(state=GroupAdmin.RemoveMember)
async def remove_member(message: types.Message, state: FSMContext):
    member_email = message.text
    admin_id = message.from_user.id

    if db.remove_member_by_email(admin_id, member_email):
        await message.answer(
            f"Участник с почтой {member_email} удален из группы.",
            reply_markup=kb.back_main_markup,
        )
    else:
        await message.answer(
            "Не удалось удалить участника. Убедитесь, что почта указана верно.",
            reply_markup=kb.back_main_markup,
        )
    await state.finish()


if __name__ == "__main__":
    google_calendar = google_calendar.GoogleCalendar(
        service_file=google_calendar.CREDENTIALS_FILE, scopes=google_calendar.SCOPES
    )
    executor.start_polling(dp, skip_updates=True)
