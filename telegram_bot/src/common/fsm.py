from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    start = State()
    registration = State()
    setup_reminders = State()
    idle = State()
