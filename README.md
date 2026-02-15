# GoFile Scanner API

Déploiement Vercel pour le scanner de liens GoFile avec webhook Discord.

## Installation

1. Clone ce repository
2. Installez Vercel CLI: `npm i -g vercel`
3. Déployez: `vercel --prod`

## API Endpoints

### POST /api/scan

Scanne des liens GoFile aléatoires ou des patterns spécifiques.

#### Parameters:
- `webhook` (string): URL du webhook Discord (optionnel)
- `count` (number): Nombre d'IDs à scanner (max 1000, défaut: 100)
- `threads` (number): Nombre de threads (max 100, défaut: 50)
- `delay` (number): Délai entre requêtes (défaut: 0.1s)
- `patterns` (boolean): Utiliser patterns communs au lieu d'IDs aléatoires (défaut: false)

#### Example:
```bash
curl -X POST https://your-domain.vercel.app/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": "https://discord.com/api/webhooks/YOUR_WEBHOOK",
    "count": 50,
    "threads": 20,
    "delay": 0.2,
    "patterns": false
  }'
```

## Features

- Scan multi-threaded de liens GoFile
- Extraction automatique des informations de fichiers
- Notifications Discord via webhook
- Support pour patterns communs
- Rate limiting intégré
- CORS activé
