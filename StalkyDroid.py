from discord import Client

from StalkyDroid.stalker import Stalker

stalker = None


def main():
    with open('StalkyDroid/discord-bot-token.txt') as f:
        token = f.read().rstrip()

    client = Client()

    @client.event
    async def on_message(message):
        if not stalker.checkMessage(message):
            return

        response = stalker.executeCommand(message)

        await client.send_message(message.channel, response)

    @client.event
    async def on_ready():
        print('Logged in as:')
        print(client.user.name)
        print(client.user.id)

        global stalker
        stalker = Stalker(client)

        print('Available channels:')
        for _id in stalker.getChannels():
            channel = client.get_channel(_id)
            print('+ ', channel.name, channel.id)

        # await client.send_message(channel, "_Bip... bip... bip..._")

    client.run(token)


if __name__ == "__main__":
    main()
