import traceback
import json
import sys

from discord.ext import commands

from core import wormcog

config = json.load(open("config.json"))


class Errors(wormcog.Wormcog):
    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):  # noqa: C901
        # ignore local handlers
        if hasattr(ctx.command, "on_error"):
            return

        # get original exception
        error = getattr(error, "original", error)

        # ignore some errors
        ignored = commands.CommandNotFound
        if isinstance(error, ignored):
            return

        # user interaction
        # fmt: off
        elif isinstance(error, commands.NotOwner):
            return await self.send(ctx, error, "You are not an owner")

        elif isinstance(error, commands.MissingRequiredArgument):
            return await self.send(ctx, error, "Missing required argument")

        elif isinstance(error, commands.BadArgument):
            return await self.send(ctx, error, "Bad argument")

        elif isinstance(error, commands.ArgumentParsingError):
            return await self.send(ctx, error, "Bad argument quotes")

        elif isinstance(error, commands.BotMissingPermissions):
            return await self.send(ctx, error, "Wormhole does not have permission to do this")

        elif isinstance(error, commands.CheckFailure):
            return await self.send(ctx, error, "You are not allowed to do this")

        elif isinstance(error, commands.CommandOnCooldown):
            return await self.send(ctx, error, f"Cooldown ({error.retry_after:.0f} s)")

        elif isinstance(error, commands.UserInputError):
            return await self.send(ctx, error, "Wrong input")

        # cog loading
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            return await self.send(ctx, error, "The cog is already loaded")
        elif isinstance(error, commands.ExtensionNotLoaded):
            return await self.send(ctx, error, "The cog is not loaded")
        elif isinstance(error, commands.ExtensionFailed):
            await self.send(ctx, error, "The cog failed")
        elif isinstance(error, commands.ExtensionNotFound):
            return await self.send(ctx, error, "No such cog")
        # fmt: on

        # print the rest
        s = "Wormhole error: {prefix}{command} by {author} in {channel}".format(
            prefix=config["prefix"],
            command=ctx.command,
            author=str(ctx.author),
            channel=ctx.channel.id if hasattr(ctx.channel, "id") else type(ctx.channel).__name__,
        )
        print(s, file=sys.stderr)
        if config["log level"] == "CRITICAL":
            return
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await self.send(ctx, error, str(error))

    async def send(self, ctx: commands.Context, error, text: str):
        if config["log level"] == "CRITICAL":
            return
        prefix = "> **Error:** "
        await ctx.send(prefix + text, delete_after=20.0)


def setup(bot):
    bot.add_cog(Errors(bot))
