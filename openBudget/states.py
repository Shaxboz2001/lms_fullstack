from aiogram.fsm.state import State, StatesGroup

class VoteStates(StatesGroup):
    waiting_phone = State()
    waiting_screenshot = State()
    waiting_confirmation = State()

class AdminStates(StatesGroup):
    waiting_project_title = State()
    waiting_project_link = State()