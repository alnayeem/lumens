// Expo config with API base injected from environment
// Usage: API_BASE=https://<cloud-run-url> npx expo start

module.exports = () => ({
  expo: {
    name: "Lumens",
    slug: "lumens-mobile",
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
    extra: {
      apiBase: process.env.API_BASE || "https://YOUR_CLOUD_RUN_URL"
    }
  }
});
