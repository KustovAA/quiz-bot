from environs import Env

from QuizBotVk import QuizBotVk


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env.str('VK_ACCESS_TOKEN')
    quiz_filepath = env.str('QUIZ_FILEPATH')

    quiz_bot = QuizBotVk(token, quiz_filepath)

    quiz_bot.run()
