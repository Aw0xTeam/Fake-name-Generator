import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from faker import Faker

# --- Configuration ---
API_TOKEN = "8332268089:AAE3oVfyhuwVgrXLYHFiNmlEUymR591U6uc"
logging.basicConfig(level=logging.INFO)

# --- FSM States ---
class NameGeneratorStates(StatesGroup):
    """States for the name generation process."""
    choosing_country = State()
    choosing_gender = State()

# --- Database Setup ---
def init_db():
    """Initializes the SQLite database and table."""
    conn = sqlite3.connect("names.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS used_names (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        gender TEXT,
        fullname TEXT UNIQUE
    )""")
    conn.commit()
    conn.close()

# --- Globals ---
locales = {
    "Nigeria🇳🇬": "en_NG",
    "Nepal🇳🇵": "ne_NP",
    "Ivory coast🇨🇮": "fr_FR",
    "Afghanistan🇦🇫": "fa_IR",
    "Bangladesh🇧🇩": "bn_BD",
    "Saudi Arabia🇸🇦": "ar_SA"
}

# --- Handlers ---
router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    """Handles the /start command, setting the initial state and keyboard."""
    await state.set_state(NameGeneratorStates.choosing_country)
    kb = [[KeyboardButton(text=c)] for c in locales.keys()]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Zaɓi ƙasa:", reply_markup=markup)

@router.message(NameGeneratorStates.choosing_country, F.text.in_(locales.keys()))
async def choose_country(message: types.Message, state: FSMContext):
    """Handles the country selection and moves to the next state."""
    await state.update_data(chosen_country=message.text)
    await state.set_state(NameGeneratorStates.choosing_gender)
    
    country = message.text
    kb = [
        [KeyboardButton(text="👨 Male"), KeyboardButton(text="👩 Female")],
        [KeyboardButton(text="⬅️ Back to Menu")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Ka zaɓi {country}. Yanzu zaɓi jinsi (gender):", reply_markup=markup)

@router.message(NameGeneratorStates.choosing_gender, F.text.in_(["👨 Male", "👩 Female", "🔄 Regenerate"]))
async def choose_gender(message: types.Message, state: FSMContext):
    """Generates and displays a fake name based on the user's choice."""
    user_data = await state.get_data()
    country_name = user_data.get('chosen_country')
    
    if message.text == "🔄 Regenerate":
        # Get the previous gender from state for regeneration
        gender_choice = user_data.get('gender_choice')
    else:
        # Get gender from the new button press
        gender_choice = "male" if "Male" in message.text else "female"
        await state.update_data(gender_choice=gender_choice) # Save for regeneration
    
    fake = Faker(locales[country_name])
    fullname = None
    
    while True:
        try:
            # Check if the name already exists before trying to insert
            candidate = f"{fake.first_name_male() if gender_choice == 'male' else fake.first_name_female()} {fake.last_name()}"
            
            conn = sqlite3.connect("names.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO used_names (country, gender, fullname) VALUES (?, ?, ?)", (country_name, gender_choice, candidate))
            conn.commit()
            conn.close()
            fullname = candidate
            break
        except sqlite3.IntegrityError:
            conn.close()
            continue # Name already exists, try again
            
    kb = [
        [KeyboardButton(text="🔄 Regenerate")],
        [KeyboardButton(text="⬅️ Back to Menu")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Sunan Bogi: <b>{fullname}</b>", reply_markup=markup)

@router.message(F.text == "⬅️ Back to Menu")
async def back_to_menu(message: types.Message, state: FSMContext):
    """Handles the 'Back to Menu' button, resetting the state."""
    await state.clear()
    await start_cmd(message, state)
    
@router.message()
async def invalid_input(message: types.Message):
    """Handles any message that doesn't match a valid command or state."""
    await message.reply("Don Allah yi amfani da maballan da aka bayar don yin zaɓi.")

# --- Main function ---
async def main():
    """Main function to run the bot."""
    init_db()
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
