from BasicBot.run import activateBot
from StalkyDroid.stalker import Stalker

if __name__ == "__main__":
    activateBot(
        'StalkyDroid/discord-bot-token.txt',
        Stalker
    )
