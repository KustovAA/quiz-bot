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

    def __init__(self, token, quiz_filepath):
        self.updater = Updater(token=token)
        self.quiz_content = get_quiz_from_file(quiz_filepath)
        self.default_markup = ReplyKeyboardMarkup(
            [['Новый вопрос', 'Сдаться']],
            one_time_keyboard=True
        )
        self.storage = redis.Redis(decode_responses=True)

    def start_handler(self, update: Update, _):
        update.message.reply_text('Привет! Сыграем в игру?', reply_markup=self.default_markup)

        return QuizBotTg.NEW_QUESTION

    def new_quiz_handler(self, update: Update, _):
        question = random.choice(list(self.quiz_content.keys()))
        self.storage.set(update.message.chat_id, question)

        update.message.reply_text(question, reply_markup=self.default_markup)

        return QuizBotTg.ANSWER

    def show_answer_handler(self, update: Update, _):
        question = self.storage.get(update.message.chat_id)
        answer = self.quiz_content[question]
        expected_answer = answer.split('(')[0].split('.')[0]

        update.message.reply_text(f'Правильный ответ: {expected_answer}', reply_markup=self.default_markup)
        self.quiz_content.pop(question)
        self.storage.delete(update.message.chat_id)

        return QuizBotTg.NEW_QUESTION

    def quiz_answer_handler(self, update, _):
        question = self.storage.get(update.message.chat_id)
        answer = self.quiz_content[question]
        user_answer = update.message.text
        expected_answer = answer.split('(')[0].split('.')[0]
        if expected_answer == user_answer:
            update.message.reply_text('Верно', reply_markup=self.default_markup)
            self.quiz_content.pop(question)
            self.storage.delete(update.message.chat_id)

            return QuizBotTg.NEW_QUESTION
        else:
            update.message.reply_text('Ошибка! попробуйте еще раз.', reply_markup=self.default_markup)
            return QuizBotTg.ANSWER

    def run(self):
        self.updater.dispatcher.add_handler(
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
