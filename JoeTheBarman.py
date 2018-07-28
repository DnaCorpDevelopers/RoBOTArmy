from BasicBot.run import activateBot
from JoeTheBarman.barman import Barman

if __name__ == "__main__":
    activateBot(
        'JoeTheBarman/discord-bot-token.txt',
        Barman
    )
