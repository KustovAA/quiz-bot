from environs import Env

from QuizBotTg import QuizBotTg


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env.str('TG_BOT_TOKEN')
    quiz_filepath = env.str('QUIZ_FILEPATH')

    quiz_bot = QuizBotTg(token, quiz_filepath)

    quiz_bot.run()
