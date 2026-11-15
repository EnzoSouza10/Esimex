import discord
from discord.ext import commands
from discord import app_commands, ui
import config


COR_HIERARQUIA = 0x546E7A
COR_FUNCAO = 0x95A5A6


def _cor_hex(role: discord.Role) -> int:
    return role.color.value if role.color else 0


def _eh_desenvolvedor(role: discord.Role) -> bool:
    return "desenvolvedor" in role.name.lower()


def _buscar_cargo_por_chave(guild: discord.Guild, chave: str):
    chave = chave.lower()
    for r in guild.roles:
        if _eh_desenvolvedor(r):
            continue
        if chave in r.name.lower():
            return r
    return None


def _mapear_cargos(guild: discord.Guild) -> dict:
    mapeamento = {
        "comandante": _buscar_cargo_por_chave(guild, "comandante"),
        "diretor": _buscar_cargo_por_chave(guild, "diretor"),
        "inspetor": _buscar_cargo_por_chave(guild, "insp"),
        "chefe": _buscar_cargo_por_chave(guild, "chefe"),
        "agente_superior": _buscar_cargo_por_chave(guild, "ag-sup"),
        "agente_junior": _buscar_cargo_por_chave(guild, "ag-jr"),
        "estagiario": _buscar_cargo_por_chave(guild, "estagiario"),
        "verificado": _buscar_cargo_por_chave(guild, "verificado"),
    }
    return mapeamento


async def _garantir_categoria(guild: discord.Guild, nome: str) -> discord.CategoryChannel:
    cat = discord.utils.get(guild.categories, name=nome)
    if cat is None:
        cat = await guild.create_category(name=nome, reason="Configuração automática CIEX Bot")
    return cat


async def _garantir_canal_texto(guild: discord.Guild, categoria: discord.CategoryChannel, nome: str) -> discord.TextChannel:
    canal = discord.utils.get(guild.text_channels, name=nome)
    if canal is None:
        canal = await guild.create_text_channel(name=nome, category=categoria, reason="Configuração automática CIEX Bot")
    elif canal.category_id != categoria.id:
        await canal.edit(category=categoria, reason="Configuração automática CIEX Bot")
    return canal


async def _aplicar_overwrites(canal: discord.TextChannel, regras: dict, guild: discord.Guild, mapeamento: dict):
    overwrites = {}
    overwrites[guild.default_role] = discord.PermissionOverwrite(
        read_messages=False,
        send_messages=False,
        read_message_history=False,
    )
    for chave, perm in regras.items():
        cargo = mapeamento.get(chave)
        if cargo is not None:
            overwrites[cargo] = perm
    try:
        await canal.edit(overwrites=overwrites, reason="Configuração automática de hierarquia CIEX Bot")
    except Exception:
        pass


class ConfirmarConfig(ui.Modal, title="⚙️ Confirmar Configuração Completa"):
    confirma = ui.TextInput(
        label="Digite CONFIRMAR para aplicar",
        placeholder="CONFIRMAR",
        required=True,
        max_length=10,
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirma.value.strip().upper() != "CONFIRMAR":
            await interaction.response.send_message("Confirmação inválida. Digite exatamente CONFIRMAR.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await _aplicar_configuracao_completa(interaction)


async def _aplicar_configuracao_completa(interaction: discord.Interaction):
    guild = interaction.guild
    mapeamento = _mapear_cargos(guild)

    configurados = []
    erros = 0

    async def adicionar(categoria_nome, canais: list):
        nonlocal erros
        try:
            cat = await _garantir_categoria(guild, categoria_nome)
        except Exception:
            erros += 1
            return
        for nome_canal, regras in canais:
            try:
                canal = await _garantir_canal_texto(guild, cat, nome_canal)
                await _aplicar_overwrites(canal, regras, guild, mapeamento)
                configurados.append(f"#{categoria_nome}/{nome_canal}")
            except Exception:
                erros += 1

    # ===== CHEGADA =====
    await adicionar("CHEGADA", [
        ("portaria", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("verificação", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("regras", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== PRINCIPAL =====
    await adicionar("PRINCIPAL", [
        ("condecorados", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("anúncios", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("constituição", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("grupo", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("hierarquia", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("comunicados-oficiais", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("calendário-institucional", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
        }),
        ("dúvidas-gerais", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== DOCUMENTAÇÕES =====
    await adicionar("DOCUMENTAÇÕES", [
        ("patrulhas", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("fardamentos", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("exames-de-admissão", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("documentos", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("manual-operacional", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("procedimentos-investigativos", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== ESTAGIÁRIOS =====
    await adicionar("ESTAGIÁRIOS", [
        ("chat-estagiários", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("avisos-estagiários", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("patrulha-estagiários", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("ficha-estagiários", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("gravações-estagiários", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("disponibilidade", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("orientações-disciplinares", {
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== AGENTES =====
    await adicionar("AGENTES", [
        ("comunicação", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("off-topic", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("mídias", {
            "verificado": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "estagiario": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("solicitar-investigação", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("justificação-de-inatividade", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("patrulhas-agentes", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== ALTO ESCALÃO =====
    await adicionar("ALTO ESCALÃO", [
        ("chat-alto-escalão", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "chefe": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("solicitação-de-black-list", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("solicitar-promoção", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "chefe": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("solicitar-punição", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("decisões-do-alto-escalão", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "chefe": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("processos-administrativos", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("avaliação-de-comando", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== ALTA CÚPULA =====
    await adicionar("ALTA CÚPULA", [
        ("chat-alta-cúpula", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "chefe": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("decisões-estratégicas", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("despachos-do-comandante", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("arquivamento-investigação", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== RELATÓRIOS =====
    await adicionar("RELATÓRIOS", [
        ("solicitar-investigação-rel", {
            "agente_junior": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("relatórios-investigações", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("promoções", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "chefe": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("rebaixamentos", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("expulsões", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("solicitação-exílios", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    # ===== LOGS =====
    await adicionar("LOGS", [
        ("registro-de-mensagens", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("registro-de-cargos", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("registro-de-punições", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("registro-de-entrada-saída", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
        ("registro-de-investigações", {
            "comandante": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "diretor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            "inspetor": discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }),
    ])

    embed = discord.Embed(
        title="📋 RELATÓRIO FINAL — CONFIGURAÇÃO COMPLETA DE HIERARQUIA",
        color=config.COLOR_DEFAULT,
    )
    embed.description = "Todas as categorias, canais e permissões foram configurados automaticamente."
    embed.add_field(name="Canais configurados", value=str(len(configurados)), inline=True)
    embed.add_field(name="Erros", value=str(erros), inline=True)
    embed.add_field(name="Cargo ignorado", value="Desenvolvedor (intocado)", inline=False)

    if mapeamento["comandante"]:
        embed.add_field(name="Comandante", value=mapeamento["comandante"].mention, inline=True)
    if mapeamento["diretor"]:
        embed.add_field(name="Diretor", value=mapeamento["diretor"].mention, inline=True)
    if mapeamento["inspetor"]:
        embed.add_field(name="Inspetor", value=mapeamento["inspetor"].mention, inline=True)
    if mapeamento["verificado"]:
        embed.add_field(name="Verificado (auxiliar)", value=mapeamento["verificado"].mention, inline=True)

    categorias_criadas = []
    for c in ["CHEGADA", "PRINCIPAL", "DOCUMENTAÇÕES", "ESTAGIÁRIOS", "AGENTES", "ALTO ESCALÃO", "ALTA CÚPULA", "RELATÓRIOS", "LOGS"]:
        if discord.utils.get(guild.categories, name=c):
            categorias_criadas.append(c)
    embed.add_field(name="Categorias", value=", ".join(categorias_criadas) if categorias_criadas else "Nenhuma", inline=False)

    if configurados:
        embed.add_field(name="Detalhe dos canais", value="\n".join(configurados[:30]), inline=False)

    embed.set_footer(text="CIEX Bot - Configuração Automática Completa")
    await interaction.followup.send(embed=embed)


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="configurar", description="Lê todos os cargos e canais e aplica configuração completa de hierarquia")
    async def configurar(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Você precisa ser administrador para usar este comando.", ephemeral=True)
            return
        await interaction.response.send_modal(ConfirmarConfig(self.bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
