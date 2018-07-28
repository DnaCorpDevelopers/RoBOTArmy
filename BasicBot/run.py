from discord import Client


def activateBot(tokenFilename: str, BotType, ):
    """
    Basic bot startup method.
    :param tokenFilename: path where the bot-token is located
    :param BotType: type of bot to instantiate
    """
    with open(tokenFilename) as f:
        token = f.read().rstrip()

    client = Client()
    bot = BotType(client)

    @client.event
    async def on_message(message):
        await bot.executeCommand(message)

    @client.event
    async def on_ready():
        await bot.login()

    client.run(token)
