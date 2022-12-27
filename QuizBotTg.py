import random

import redis
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    ConversationHandler,
    CommandHandler,
)
from telegram import ReplyKeyboardMarkup, Update

from utils import get_quiz_from_file


class QuizBotTg:
    NEW_QUESTION, ANSWER = range(2)

    def __init__(self, token, quiz_filepath, storage_engine='redis'):
        self.updater = Updater(token=token)
        self.quiz_content = get_quiz_from_file(quiz_filepath)
        self.default_markup = ReplyKeyboardMarkup(
            [['Новый вопрос', 'Сдаться']],
            one_time_keyboard=True
        )
        if storage_engine == 'redis':
            self.storage = redis.Redis(decode_responses=True)

    @property
    def dispatcher(self):
        return self.updater.dispatcher

    def send_message(self, update, text):
        return update.message.reply_text(text, reply_markup=self.default_markup)

    def start_handler(self, update: Update, _):
        self.send_message(update, 'Привет! Сыграем в игру?')

        return QuizBotTg.NEW_QUESTION

    def new_quiz_handler(self, update: Update, _):
        question = random.choice(list(self.quiz_content.keys()))
        self.storage.set(update.message.chat_id, question)

        self.send_message(update, question)

        return QuizBotTg.ANSWER

    def show_answer_handler(self, update: Update, _):
        question = self.storage.get(update.message.chat_id)
        answer = self.quiz_content[question]
        expected_answer = answer.split('(')[0].split('.')[0]

        self.send_message(update, f'Правильный ответ: {expected_answer}')
        self.quiz_content.pop(question)
        self.storage.delete(update.message.chat_id)

        return QuizBotTg.NEW_QUESTION

    def quiz_answer_handler(self, update, _):
        question = self.storage.get(update.message.chat_id)
        answer = self.quiz_content[question]
        user_answer = update.message.text
        expected_answer = answer.split('(')[0].split('.')[0]
        if expected_answer == user_answer:
            self.send_message(update, 'Верно')
            self.quiz_content.pop(question)
            self.storage.delete(update.message.chat_id)

            return QuizBotTg.NEW_QUESTION
        else:
            self.send_message(update, 'Ошибка! попробуйте еще раз.')
            return QuizBotTg.ANSWER

    def run(self):
        self.dispatcher.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler('start', self.start_handler)],
                states={
                    QuizBotTg.NEW_QUESTION: [
                        MessageHandler(
                            Filters.regex('^Новый вопрос$'),
                            self.new_quiz_handler
                        ),
                        MessageHandler(
                            Filters.regex('^Сдаться$'),
                            self.show_answer_handler
                        )
                    ],
                    QuizBotTg.ANSWER: [
                        MessageHandler(
                            Filters.text & ~Filters.regex('^Сдаться$'),
                            self.quiz_answer_handler
                        ),
                        MessageHandler(
                            Filters.regex('^Сдаться$'),
                            self.show_answer_handler
                        )
                    ]
                },
                fallbacks=[]
            )
        )

        self.updater.start_polling()
        self.updater.idle()
