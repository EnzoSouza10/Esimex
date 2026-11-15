import discord
from discord.ext import commands
from discord import app_commands, ui
import config


class PromocaoView(discord.ui.View):
    def __init__(self, membros: list, cargos: list, promotor: discord.Member):
        super().__init__(timeout=120)
        self.membros = membros
        self.cargos = cargos
        self.promotor = promotor
        self.membro_escolhido = None
        self.cargo_escolhido = None

        self.membro_select = discord.ui.Select(
            placeholder="Escolha o membro para promover",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id), description=m.name) for m in membros[:25]],
            min_values=1,
            max_values=1,
        )
        self.cargo_select = discord.ui.Select(
            placeholder="Escolha o cargo para adicionar",
            options=[discord.SelectOption(label=c.name, value=str(c.id), description=f"ID: {c.id}") for c in cargos[:25]],
            min_values=1,
            max_values=1,
        )

        self.membro_select.callback = self._on_membro
        self.cargo_select.callback = self._on_cargo

        self.add_item(self.membro_select)
        self.add_item(self.cargo_select)

        self.confirmar = discord.ui.Button(label="Confirmar Promoção", style=discord.ButtonStyle.success)
        self.confirmar.callback = self._on_confirmar
        self.add_item(self.confirmar)

    async def _on_membro(self, interaction: discord.Interaction):
        self.membro_escolhido = int(self.membro_select.values[0])
        await interaction.response.defer()

    async def _on_cargo(self, interaction: discord.Interaction):
        self.cargo_escolhido = int(self.cargo_select.values[0])
        await interaction.response.defer()

    async def _on_confirmar(self, interaction: discord.Interaction):
        if not self.membro_escolhido or not self.cargo_escolhido:
            await interaction.response.send_message("Selecione um membro e um cargo antes de confirmar.", ephemeral=True)
            return

        guild = interaction.guild
        membro = guild.get_member(self.membro_escolhido)
        cargo = guild.get_role(self.cargo_escolhido)

        if not membro or not cargo:
            await interaction.response.send_message("Membro ou cargo não encontrado.", ephemeral=True)
            return

        try:
            await membro.add_roles(cargo, reason=f"Promoção por {self.promotor}")
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para adicionar este cargo.", ephemeral=True)
            return

        embed = discord.Embed(title="🎖️ Promoção Realizada", color=config.COLOR_SUCCESS)
        embed.add_field(name="Membro promovido", value=membro.mention, inline=True)
        embed.add_field(name="Cargo adicionado", value=cargo.mention, inline=True)
        embed.add_field(name="Promovido por", value=self.promotor.mention, inline=True)
        embed.add_field(name="ID Membro", value=str(membro.id), inline=True)
        embed.add_field(name="ID Cargo", value=str(cargo.id), inline=True)
        embed.set_footer(text="CIEX Bot - Sistema de Promoções")
        await interaction.response.edit_message(embed=embed, view=None)


class Promotions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="promoção", description="Promover um membro adicionando um cargo")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def promocao(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        membros = [m for m in guild.members if not m.bot]
        cargos = [r for r in guild.roles if r != guild.default_role and r < guild.me.top_role]

        if not membros:
            await interaction.followup.send("Não há membros disponíveis para promover.", ephemeral=True)
            return
        if not cargos:
            await interaction.followup.send("Não há cargos disponíveis para adicionar.", ephemeral=True)
            return

        view = PromocaoView(membros, cargos, interaction.user)
        embed = discord.Embed(title="🎖️ Sistema de Promoção", color=config.COLOR_DEFAULT)
        embed.description = "Selecione o membro e o cargo abaixo, depois clique em **Confirmar Promoção**."
        embed.add_field(name="Membros disponíveis", value=str(len(membros)), inline=True)
        embed.add_field(name="Cargos disponíveis", value=str(len(cargos)), inline=True)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Promotions(bot))
