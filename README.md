# Telegram Media Downloader Bot

```
docker build -t media_bot .

docker run -d `
  --name tg-down `
  --restart unless-stopped `
  -e BOT_TOKEN="TOKEN" `
  -v ./downloads:/app/downloads `
  tg-down-bot

```

Поддержка Instagram (Cookies)
cookies.txt из браузера добавить через: -v ${PWD}/cookies.txt:/app/cookies.txt:ro
