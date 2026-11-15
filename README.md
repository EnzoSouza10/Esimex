# CIEX Bot

Bot de verificação Discord + Roblox, promoções e configuração automática de hierarquia de canais.

## Deploy gratuito 24h (Render)

1. Crie um repositório no GitHub e envie este código (não envie o `.env`).
2. No [Render](https://render.com), crie um **Background Worker** conectado ao seu repositório.
3. Adicione a variável de ambiente:
   - `TOKEN` = token do seu bot Discord
4. O comando de início já está no `Procfile`: `python bot/main.py`

## Variáveis de ambiente (.env)

Copie `.env.example` para `.env` e preencha:

```
TOKEN=seu_token_aqui
PREFIX=!
GUILD_ID=seu_id_do_servidor
```

Não commite o `.env`.
