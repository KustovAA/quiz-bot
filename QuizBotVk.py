import random

import redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType

from utils import get_quiz_from_file


class QuizBotVk:
    NEW_QUESTION, ANSWER = range(2)

    def __init__(self, token, quiz_filepath):
        vk_session = vk.VkApi(token=token)
        self.vk_api = vk_session.get_api()
        self.longpoll = VkLongPoll(vk_session)
        self.quiz_content = get_quiz_from_file(quiz_filepath)
        self.state = None
        self.keyboard = VkKeyboard(one_time=True)
        self.keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
        self.keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
        self.storage = redis.Redis(decode_responses=True)

    def send_message(self, text, event):
        self.vk_api.messages.send(
            user_id=event.user_id,
            message=text,
            random_id=get_random_id(),
            keyboard=self.keyboard.get_keyboard(),
        )

    def start_handler(self, event):
        self.send_message('Привет! Сыграем в игру?', event)

    def new_quiz_handler(self, event):
        question = random.choice(list(self.quiz_content.keys()))
        self.storage.set(event.user_id, question)

        self.send_message(question, event)
        self.state = QuizBotVk.ANSWER

    def show_answer_handler(self, event):
        question = self.storage.get(event.user_id)
        if not question:
            self.send_message('Нет вопроса', event)
            return

        answer = self.quiz_content[question]
        expected_answer = answer.split('(')[0].split('.')[0]

        self.send_message(f'Правильный ответ: {expected_answer}', event)
        self.quiz_content.pop(question)
        self.storage.delete(event.user_id)
        self.state = QuizBotVk.NEW_QUESTION

    def quiz_answer_handler(self, event):
        question = self.storage.get(event.user_id)
        answer = self.quiz_content[question]
        user_answer = event.text
        expected_answer = answer.split('(')[0].split('.')[0]
        if expected_answer == user_answer:
            self.send_message('Верно', event)
            self.quiz_content.pop(question)
            self.storage.delete(event.user_id)

            self.state = QuizBotVk.NEW_QUESTION
        else:
            self.send_message('Ошибка! попробуйте еще раз.', event)

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == "Сдаться":
                    self.show_answer_handler(event)
                elif event.text == "Новый вопрос":
                    self.new_quiz_handler(event)
                elif self.state == QuizBotVk.ANSWER:
                    self.quiz_answer_handler(event)
                else:
                    self.state = QuizBotVk.NEW_QUESTION
                    self.send_message('Выберите действие', event)
