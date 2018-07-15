import discord

from JoeTheBarman.barman import Barman

barman = None


def main():
    with open('discord-bot-token.txt') as f:
        token = f.read().rstrip()

    client = discord.Client()

    @client.event
    async def on_message(message):
        if not barman.checkMessage(message):
            return

        msg, img = barman.serveDrinks(message)

        await client.send_message(message.channel, msg)

        if img is not None:
            await client.send_file(message.channel, img)

    @client.event
    async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)

        global barman
        barman = Barman(client)

        # await client.send_message(barman.channel, barman.greetings())

    client.run(token)


if __name__ == "__main__":
    main()
