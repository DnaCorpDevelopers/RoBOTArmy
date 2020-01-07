from discord.ext import commands


class Manage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='anchor')
    async def something(self, ctx):
        await ctx.send('Doing! :)')


def setup(bot):
    bot.add_cog(Manage(bot))
