import telebot
import logging
from datetime import datetime
# from telebot import types
import json
import uuid
import os
import sys
import openai
import threading
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TOKEN')
me = os.getenv('ME')
openai.api_key = os.getenv('GBT')

bot = telebot.TeleBot(token)

random_filename = str(uuid.uuid4())

with open("main.json", "r", encoding="utf-8") as file:
    main_json_texts = json.load(file)
welcome_message = main_json_texts["welcome_message"]

timeout_duration = 69


def logging_func():
    logging.basicConfig(filename='app.log',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    logging.basicConfig(filename='app.log',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.INFO, stream=sys.stdout)


# Function to handle timeout
def timeout_callback(message):
    bot.reply_to(message, "Timeout: No response received.")
    python = sys.executable
    os.execl(python, python, *sys.argv)


def set_timer(message, timeout_duration):
    timer = threading.Timer(timeout_duration, timeout_callback,
                            args=(message,))
    timer.start()
    return timer


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, f'{welcome_message}')


@bot.message_handler(commands=["set_goal"])
def set_goal_start(message):
    username_finder(message)
    username_original = message.from_user.username
    bot.reply_to(message, f'your goal?\n'
                 f'({timeout_duration} sec to answer)')
    timer = set_timer(message, timeout_duration)
    bot.register_next_step_handler(message, set_goal, username_original, timer)


def set_goal(message, username_original, timer):
    # Define a filter to check if the message is from the original user
    def is_original_user(msg):
        return msg.from_user.username == username_original
    # Check if the message is from the original user
    if is_original_user(message):
        # Process the user's goal
        if message.content_type == 'text':
            goal_answer = message.text.strip().lower()

            if goal_answer in ["/set_goal", "/start@qeir_bot",
                               "/set_goal@qeir_bot", "/dice@qeir_bot"]:
                error404(message)
                bot.reply_to(message, 'your goal?')
                bot.register_next_step_handler(message, set_goal,
                                               username_original, timer)
            else:
                timer.cancel()
                bot.reply_to(message, f'Goal set to "{goal_answer}". '
                             'Now, please provide the date.')
                # Move to the next step
                timer = set_timer(message, timeout_duration)
                bot.register_next_step_handler(message, set_date,
                                               username_original,
                                               goal_answer, timer)
        else:
            # Ask the user to provide the goal in text format
            bot.reply_to(message, 'Please provide your goal in text format.')
            bot.register_next_step_handler(message, set_goal,
                                           username_original, timer)
    else:
        # Ignore messages from other users, but continue the conversation
        error404(message)
        bot.register_next_step_handler(message, set_goal,
                                       username_original, timer)


def set_date(message, username_original, goal_answer, timer):
    # Define a filter to check if the message is from the original user
    def is_original_user(msg):
        return msg.from_user.username == username_original

    if is_original_user(message):
        if message.content_type == 'text':
            date_answer = message.text.strip().lower()

            if date_answer in ["/set_goal", "/start@qeir_bot",
                               "/set_goal@qeir_bot"]:
                error404(message)
                bot.reply_to(message, 'your date?')
                bot.register_next_step_handler(message, set_date,
                                               username_original, goal_answer)
            else:
                timer.cancel()
                bot.reply_to(message, f'Date set to "{date_answer}"!')
                succes404(message, goal_answer, date_answer)
        else:
            bot.reply_to(message, 'Please provide your date in text format')
            bot.register_next_step_handler(message, set_date,
                                           username_original, goal_answer)
    else:
        # Ignore messages from other users, but continue the conversation
        error404(message)
        bot.register_next_step_handler(message, set_date,
                                       username_original, goal_answer)


# @bot.message_handler(func=lambda message: True)
def username_finder(message):
    # Extract the username from the message
    username = message.from_user.username

    # Do something with the username
    bot.reply_to(message, "The username of the user "
                 f"interacting with the bot is: @{username}")


def error404(message):
    bot.reply_to(message, "error, try again")


def succes404(message, goal_answer, date_answer):
    user = message.from_user
    username = message.from_user.username
    user_id = user.id
    profile_photos = bot.get_user_profile_photos(user_id)
    response = (f"Done, {username}!\nGoal: {goal_answer}\nDate: {date_answer}")
    if profile_photos and profile_photos.photos:
        latest_photo = profile_photos.photos[0][0]
        file_id = latest_photo.file_id
        bot.send_photo(message.chat.id, file_id, caption=response)
        # bot.send_message(message.chat.id, response)
        # bot.reply_to(message, response)
    else:
        bot.send_message(message.chat.id, response)


def record_message(user_id, username, message_text):
    # Define the filename for the JSON file
    filename = "user_messages.json"

    # Load existing data from the JSON file, if it exists
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, initialize an empty dictionary
        data = {}

    # Get the current timestamp
    timestamp = datetime.now().isoformat()

    # Append the new message to the data dictionary
    if str(user_id) in data:
        data[str(user_id)]["messages"].append({
            "text": message_text,
            "timestamp": timestamp
        })
    else:
        data[str(user_id)] = {
            "username": username,
            "messages": [{
                "text": message_text,
                "timestamp": timestamp
            }]
        }

    # Write the updated data back to the JSON file
    with open(filename, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


@bot.message_handler(commands=["dice"])
def rolladice(message):
    bot.reply_to(message, "here you go:")
    bot.send_dice(message.chat.id, emoji="🎲")


# =================== gbt ===================
@bot.message_handler(commands=["aiaiai"])
# @bot.message_handler(func=lambda message: True)
def testai(message):
    bot.reply_to(message, "hi")
    # Get user input
    user_input = message.text.strip().lower()

    # Generate response using OpenAI
    response = generate_response(user_input)

    # Send the response back to the user
    bot.reply_to(message, response)


def generate_response(input_text):
    response = openai.Completion.create(
        engine="davinci",
        prompt=input_text,
        max_tokens=50
    )
    generated_text = response.choices[0].text.strip()
    return generated_text
# =================== gbt ===================


@bot.message_handler(func=lambda message: True)
def bigbrother(message):
    # Call the record_message function to record the message
    record_message(message.from_user.id, message.from_user.username,
                   message.text)
    # print(f"Received message from {message.from_user.username}: "
    # "{message.text}")


logging_func()

bot.infinity_polling(timeout=10, long_polling_timeout=5)
bot.polling(none_stop=True)
