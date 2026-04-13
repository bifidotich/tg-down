# Telegram Media Downloader Bot

```
docker build -t tg-down .

docker run -d `
  --name tg-down `
  --restart unless-stopped `
  -e BOT_TOKEN="TOKEN" `
  -v ./downloads:/app/downloads `
  tg-down-bot

```

Поддержка Instagram (Cookies)
cookies.txt из браузера добавить через: -v ./cookies.txt:/app/cookies.txt:ro
