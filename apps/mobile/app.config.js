// Expo config with API base injected from environment
// Usage: API_BASE=https://<cloud-run-url> npx expo start

// Lightweight .env loader (no extra dependency)
// Loads apps/mobile/.env.local then .env if present
try {
  const fs = require('fs');
  const path = require('path');
  const envPaths = [
    path.join(__dirname, '.env.local'),
    path.join(__dirname, '.env'),
  ];
  for (const p of envPaths) {
    if (!fs.existsSync(p)) continue;
    const lines = fs.readFileSync(p, 'utf8').split(/\r?\n/);
    for (const raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
      if (!m) continue;
      const key = m[1];
      let val = m[2];
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith('\'') && val.endsWith('\''))) {
        val = val.slice(1, -1);
      }
      if (process.env[key] === undefined) process.env[key] = val;
    }
  }
} catch {}

module.exports = () => ({
  expo: {
    name: "Lumens",
    slug: "lumens-mobile",
    owner: process.env.EXPO_OWNER || process.env.EXPO_PUBLIC_EXPO_OWNER || undefined,
    version: "0.1.0",
    // Match installed Expo Go (SDK 54). Remove or keep in sync.
    sdkVersion: "54.0.0",
    orientation: "portrait",
    // Optionally add app icons under ./assets and reference here
    userInterfaceStyle: "automatic",
    // splash: { image: "./assets/splash.png", resizeMode: "contain", backgroundColor: "#ffffff" },
    updates: {
      fallbackToCacheTimeout: 0
    },
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true
    },
    android: {},
    web: {
      bundler: "metro"
    },
    plugins: [
      'expo-web-browser'
    ],
    extra: {
      apiBase: process.env.API_BASE || "https://lumens-api-4qubw3p5lq-uc.a.run.app",
      googleExpoClientId: process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID || undefined,
      googleAndroidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || undefined,
      googleIosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || undefined,
      googleWebClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || undefined
    }
  }
});
