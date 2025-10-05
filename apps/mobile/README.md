# Lumens Mobile (Expo)

A minimal React Native (Expo) app that consumes the Lumens API.

## Prerequisites
- Node.js 18+
- Android Studio (emulator) or a real Android device with Expo Go
- Your API deployed and reachable (Cloud Run `lumens-api` URL)

## Configure API base
Set the Cloud Run URL via env var for Expo:

```
cd apps/mobile
export API_BASE=https://<your-cloud-run-url>
```

`app.config.js` injects this into `expo.extra.apiBase` used by the app.

## Run
```
npm install
npx expo start
```
- Press `a` to launch Android emulator, or scan the QR in Expo Go on device.

## What’s included
- Categories screen (fetches `/v1/categories`)
- Feed screen with infinite scroll (fetches `/v1/content?topic=...&language=en`)
- Tap a card to open the video in the YouTube app/site (creator-friendly)

## Notes
- For local API during development:
  - Android emulator: use `http://10.0.2.2:8000` as API_BASE
  - Real device: use your machine’s LAN IP (e.g., `http://192.168.1.50:8000`)
- To embed inline, you can add a WebView using `item.embed`, but opening the YouTube app is better for creator monetization.

