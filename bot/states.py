from aiogram.dispatcher.filters.state import StatesGroup, State


class LoginFrom(StatesGroup):
    waiting_for_calendar_id = State()


class CreateEvent(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_start_time = State()
    waiting_for_duration = State()
    waiting_for_description = State()


class CreateGroupEvent(StatesGroup):
    waiting_for_title = State()
    waiting_for_duration = State()
    waiting_for_description = State()


class EditEventState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_date = State()
    waiting_for_new_start = State()
    waiting_for_new_duration = State()
    waiting_for_new_description = State()


class EditGroupEventState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_date = State()
    waiting_for_new_start = State()
    waiting_for_new_duration = State()
    waiting_for_new_description = State()


class GroupCreation(StatesGroup):
    waiting_for_group_name = State()

class GroupAdmin(StatesGroup):
    RemoveMember = State()
