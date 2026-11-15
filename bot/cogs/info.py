import discord
from discord.ext import commands
from discord import app_commands, ui
import config
import requests
from datetime import datetime, timezone


def _resolver_id_por_nome(username: str):
    try:
        resp = requests.post(config.ROBLOX_USERS_URL, json={"usernames": [username]}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    for usuario in data.get("data", []):
        if usuario.get("name", "").lower() == username.lower():
            return usuario.get("id")
    return None


def _buscar_info_roblox(user_id: int):
    try:
        resp = requests.get(config.ROBLOX_USER_INFO_URL.format(user_id=user_id), timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _buscar_badges(user_id: int):
    try:
        resp = requests.get(config.ROBLOX_BADGES_URL.format(user_id=user_id), timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception:
        return []


def _badge_image_url(badge_id: int) -> str:
    return config.ROBLOX_BADGE_IMAGE_URL.format(badge_id=badge_id)


class VerificarModal(ui.Modal, title="🔍 Verificação de Usuário"):
    usuario_discord = ui.TextInput(
        label="Usuário do Discord",
        placeholder="Nome ou ID do Discord",
        required=False,
        max_length=100,
    )
    usuario_roblox = ui.TextInput(
        label="Usuário do Roblox",
        placeholder="Nick do Roblox",
        required=False,
        max_length=100,
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = await self._montar_relatorio(interaction, self.usuario_discord.value.strip(), self.usuario_roblox.value.strip())
        await interaction.followup.send(embed=embed)

    async def _montar_relatorio(self, interaction, nome_discord: str, nome_roblox: str):
        agora = datetime.now(timezone.utc)
        embed = discord.Embed(
            title="📋 RELATÓRIO DE VERIFICAÇÃO",
            color=config.COLOR_DEFAULT,
            timestamp=agora,
        )
        embed.set_author(name="CIEX Bot - Verificação", icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None)
        embed.description = "Preencha os dados abaixo para conferir informações da conta."

        tem_discord = bool(nome_discord)
        tem_roblox = bool(nome_roblox)

        if not tem_discord and not tem_roblox:
            embed.description = "⚠️ Informe ao menos um nome de usuário."
            embed.color = config.COLOR_WARNING
            return embed

        if tem_discord:
            membro = None
            try:
                membro = await interaction.guild.fetch_member(int(nome_discord))
            except (ValueError, discord.NotFound, discord.HTTPException):
                for m in interaction.guild.members:
                    if m.name.lower() == nome_discord.lower() or m.display_name.lower() == nome_discord.lower():
                        membro = m
                        break

            if membro:
                dias_conta = (agora - membro.created_at).days
                dias_servidor = (agora - membro.joined_at).days if membro.joined_at else None
                conta_recente = dias_conta <= config.RECENT_ACCOUNT_DAYS
                status_emoji = "🚩" if conta_recente else "✅"
                status_txt = "Conta recente" if conta_recente else "Conta estabelecida"
                cor_discord = config.COLOR_ERROR if conta_recente else config.COLOR_SUCCESS

                embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="👤 **DISCORD**", inline=False)
                embed.add_field(name="Membro", value=membro.mention, inline=True)
                embed.add_field(name="ID", value=str(membro.id), inline=True)
                embed.add_field(name="Nome", value=membro.name, inline=True)
                embed.add_field(name="Apelido", value=membro.display_name, inline=True)
                embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
                embed.add_field(name="Idade da conta", value=f"{dias_conta} dia(s)", inline=True)
                if dias_servidor is not None:
                    embed.add_field(name="Tempo no servidor", value=f"{dias_servidor} dia(s)", inline=True)
                embed.add_field(name="Cargo mais alto", value=membro.top_role.mention, inline=True)
                embed.add_field(name="Status", value=f"{status_emoji} {status_txt}", inline=False)
                embed.set_thumbnail(url=membro.display_avatar.url)
                embed.color = cor_discord
            else:
                embed.add_field(name="👤 Discord", value=f"`{nome_discord}` não encontrado no servidor.", inline=False)

        if tem_roblox:
            user_id = _resolver_id_por_nome(nome_roblox)
            if user_id:
                info = _buscar_info_roblox(user_id)
                badges = _buscar_badges(user_id)

                exibicao = info.get("displayName", "Desconhecido") if info else "Desconhecido"
                criado_roblox = info.get("created", "")[:10] if info else "Desconhecido"

                embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="🎮 **ROBLOX**", inline=False)
                embed.add_field(name="Usuário", value=nome_roblox, inline=True)
                embed.add_field(name="ID Roblox", value=str(user_id), inline=True)
                embed.add_field(name="Nome de exibição", value=exibicao, inline=True)
                embed.add_field(name="Badges", value=str(len(badges)), inline=True)
                embed.add_field(name="Conta criada", value=criado_roblox, inline=True)

                if badges:
                    primeiro_badge = badges[0]
                    badge_id = primeiro_badge.get("id")
                    if badge_id:
                        embed.set_image(url=_badge_image_url(badge_id))
                        embed.add_field(name="🏆 Badge em destaque", value=f"ID: `{badge_id}`", inline=False)

                    outras = [f"`{b.get('id')}`" for b in badges[1:6]]
                    if outras:
                        embed.add_field(name="Outras badges", value=" ".join(outras), inline=False)
                else:
                    embed.add_field(name="Badges", value="Nenhuma badge pública encontrada.", inline=False)
                embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png")
            else:
                embed.add_field(name="🎮 Roblox", value=f"`{nome_roblox}` não encontrado.", inline=False)

        embed.set_footer(text=f"Verificado por {interaction.user}", icon_url=interaction.user.display_avatar.url)
        return embed


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="verificar", description="Abre formulário para verificar Discord e Roblox juntos")
    async def verificar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificarModal(self.bot))

    @app_commands.command(name="relatorio", description="Exibe relatório atual de cargos e canais do servidor")
    async def relatorio(self, interaction: discord.Interaction):
        guild = interaction.guild
        todos = [r for r in guild.roles if r != guild.default_role]
        embed = discord.Embed(title="📊 Relatório do Servidor", color=config.COLOR_INFO)
        embed.add_field(name="Total de cargos", value=str(len(todos)), inline=True)
        embed.add_field(name="Canais de texto", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Categorias", value=str(len(guild.categories)), inline=True)
        embed.set_footer(text="CIEX Bot")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
