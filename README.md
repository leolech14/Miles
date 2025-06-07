# Miles - Telegram Bonus Alert Bot

This bot checks several mileage blogs for transfer bonus promotions and sends
Telegram notifications when new deals appear.

Environment variables:

- `TELEGRAM_BOT_TOKEN` – bot token used to send messages
- `TELEGRAM_CHAT_ID` – default chat to notify
- `MIN_BONUS` – minimum bonus percentage to alert (default 80)
- `SOURCES_PATH` – path to the YAML file with program sources
- `OPENAI_API_KEY` – required for the `/chat` command

## Quick start

1. Configure the secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `MIN_BONUS`,
   `FLY_API_TOKEN` and optionally `SOURCES_PATH` in your GitHub repository.

2. Create the Fly.io app (run once):

   ```bash
   flyctl apps create miles
   ```
3. Deploy to Fly.io with a single command:

   ```bash
   gh workflow run deploy-fly
   ```

To run everything locally:

```bash
docker compose up
```

After cloning the repository, run `pre-commit install` to enable local checks.

Edit `sources.yaml` to change which pages are scanned.

### Runtime commands

| Command | Action |
|---------|--------|
| `/ask` | Run an immediate promotion scan |
| `/sources` | List current sources |
| `/addsrc <url>` | Add a new source URL |
| `/rmsrc <id_or_url>` | Remove a source by index or full URL |
| `/update` | Search the web for new sources |
| `/chat <text>` | Talk with the integrated AI assistant |

## ChatGPT mode

Use `/chat <message>` to converse with the bot. The conversation is kept per
Telegram user in Redis for up to 30 minutes. Send `/end` to clear the stored
context. Set `OPENAI_API_KEY` to enable this feature.

## Example sources

- **Melhores Destinos**<br>
  Portal brasileiro que publica diariamente promoções de bônus de transferência (Livelo, Esfera, Iupp etc.) e envia alertas imediatos via app, push, Telegram e newsletter.
  > "Se tem promoção de transferência bonificada na área, tem condição boa para comprar milhas mais baratas..."<br>
  Fonte: <https://www.melhoresdestinos.com.br/milhas/pontos-dinheiro-bonus-livelo-smiles-maio25>

- **Passageiro de Primeira**<br>
  Blog especializado em programas de fidelidade; divulga transferências bonificadas em tempo real, traz análises detalhadas e oferece grupos de Telegram, WhatsApp e notificações por aplicativo.
  > "Relembramos as melhores promoções de transferências bonificadas de pontos que ocorreram em 2024"<br>
  Fonte: <https://passageirodeprimeira.com/retrospectiva-promocoes-de-transferencias-bonificadas-2024/>

- **Pontos pra Voar**<br>
  Site que cobre promoções de milhas, cartões e hotéis; publica tabelas comparativas de bônus de transferência e avisa assinantes por newsletter, Telegram ou feed RSS.
  > "Receba até 80% de bônus na transferência de pontos do Itaú para o Azul Fidelidade"<br>
  Fonte: <https://pontospravoar.com/receba-ate-80-porcento-bonus-transferencia-pontos-itau-azul-fidelidade/>

- **Mestre das Milhas**<br>
  Portal focado em maximizar milhas; posta rapidamente campanhas de bônus de transferência, calcula custos e mantém canal no Telegram para alertas instantâneos.
  > "Livelo oferece até 110% de bônus na transferência de pontos para a Smiles"<br>
  Fonte: <https://mestredasmilhas.com/livelo-oferece-ate-110-de-bonus-na-transferencia-de-pontos-para-a-smiles/>

- **Guia do Milheiro**<br>
  Agregador brasileiro que reúne promoções de transferência bonificada, explica regras, mostra passo a passo e envia avisos por newsletter ou Telegram.
  > "Azul Fidelidade oferece até 80% de bônus na transferência de pontos – veja como participar"<br>
  Fonte: <https://guiadomilheiro.com.br/azul-fidelidade-oferece-ate-80-de-bonus-na-transferencia-de-pontos-veja-como-participar/>

## Development

Run the checks before committing:

```bash
pytest -q
mypy --strict miles/
```
