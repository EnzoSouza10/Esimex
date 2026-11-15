import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands
from discord import app_commands

import config


class CIEXBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        for cog in ["cogs.info", "cogs.promotions", "cogs.config"]:
            await self.load_extension(cog)

        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"Conectado como {self.user} (ID: {self.user.id})")
        print("------")


bot = CIEXBot()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você não tem permissão para usar este comando.", ephemeral=True)
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send(f"Ocorreu um erro: {error}")


if __name__ == "__main__":
    bot.run(config.TOKEN)
