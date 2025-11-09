# Lumens Mobile App - Testing Guide

## Overview
The Lumens mobile app is a React Native application built with Expo that provides a video browsing experience for Islamic content. It includes authentication, category browsing, video feeds, and a TikTok-style swipe player.

## Prerequisites

### 1. Node.js and npm
- **Required**: Node.js 18 or higher
- Check version: `node --version` and `npm --version`
- Install from: https://nodejs.org/

### 2. Expo CLI and Expo Go App
- **Expo CLI**: Installed globally or via npx (recommended)
- **Expo Go App**: 
  - iOS: Download from App Store
  - Android: Download from Google Play Store
- Install Expo CLI: `npm install -g expo-cli` (optional, npx works too)

### 3. Development Environment Options

#### Option A: Physical Device (Recommended for best experience)
- Install Expo Go on your phone
- Ensure phone and computer are on the same WiFi network

#### Option B: Android Emulator
- Install Android Studio: https://developer.android.com/studio
- Set up an Android Virtual Device (AVD)
- Ensure Android SDK and platform tools are installed

#### Option C: iOS Simulator (macOS only)
- Install Xcode from App Store
- Install iOS Simulator via Xcode

## Setup Instructions

### 1. Install Dependencies
```bash
cd apps/mobile
npm install
```

### 2. Configure API Base URL
The app needs to know where your API server is located.

**Set the API base URL:**
```bash
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
```

**For local API development:**
- Android Emulator: `export API_BASE=http://10.0.2.2:8000`
- Real Device: `export API_BASE=http://YOUR_LOCAL_IP:8000` (e.g., `http://192.168.1.50:8000`)
- iOS Simulator: `export API_BASE=http://localhost:8000`

**Permanent configuration (optional):**
You can also update `app.config.js` line 30 to set a default:
```javascript
apiBase: process.env.API_BASE || "https://lumens-api-4qubw3p5lq-uc.a.run.app",
```

### 3. Configure Google OAuth (Optional)
If you want to test Google Sign-In, you need to set up OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials for your project
3. Set environment variables:
```bash
export EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID=your-expo-client-id
export EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=your-android-client-id
export EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=your-ios-client-id
export EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=your-web-client-id
```

**Note**: Email sign-in works without OAuth setup (stores email locally only).

## Running the App

### Start the Development Server
```bash
cd apps/mobile
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
npx expo start
```

This will:
- Start the Metro bundler
- Display a QR code
- Show options to open on different platforms

### Platform-Specific Commands

**Android Emulator:**
```bash
npx expo start --android
# Or press 'a' in the Expo CLI
```

**iOS Simulator (macOS only):**
```bash
npx expo start --ios
# Or press 'i' in the Expo CLI
```

**Web Browser:**
```bash
npx expo start --web
# Or press 'w' in the Expo CLI
```

**Physical Device:**
1. Open Expo Go app on your phone
2. Scan the QR code displayed in the terminal
3. The app will load on your device

## Testing Checklist

### 1. Authentication Screen
- [ ] App starts and shows login screen
- [ ] Email input field is visible and functional
- [ ] Can sign in with email (any email format with @ works)
- [ ] Google Sign-In button is visible (may not work without OAuth setup)
- [ ] After sign-in, navigates to Latest screen
- [ ] Sign-out button works and returns to login

### 2. Latest Screen
- [ ] Videos load from API
- [ ] Featured video player is displayed at top
- [ ] Video grid shows thumbnail, title, and channel
- [ ] Can scroll through videos
- [ ] Infinite scroll loads more videos when reaching bottom
- [ ] Loading indicator appears while fetching
- [ ] Tapping a video updates the featured player
- [ ] Selected video has border highlight
- [ ] User email is displayed at top
- [ ] Sign out button works

### 3. Categories Screen
- [ ] Categories load from API
- [ ] List shows: Prophets, Duas & Supplications, Ramadan, Seerah, Nasheeds
- [ ] Tapping a category navigates to Feed screen
- [ ] Navigation back button works

### 4. Feed Screen
- [ ] Videos load for selected topic
- [ ] Grid layout displays correctly (2 columns)
- [ ] Thumbnails load and display
- [ ] Video titles and channel names show
- [ ] Infinite scroll works
- [ ] Tapping a video navigates to Swipe Player
- [ ] Loading states work correctly
- [ ] Error handling displays messages

### 5. Swipe Player Screen
- [ ] Videos load for the topic
- [ ] Video player displays correctly
- [ ] Can swipe horizontally between videos
- [ ] Only the visible video plays
- [ ] Videos autoplay when scrolled into view
- [ ] Initial video ID is respected (if provided)
- [ ] Infinite scroll loads more videos
- [ ] Loading indicator shows while fetching

### 6. Player Screen (if accessible)
- [ ] Video player displays
- [ ] Play/pause controls work
- [ ] "Open in YouTube" link works
- [ ] Navigation works correctly

### 7. Network and Error Handling
- [ ] App handles API errors gracefully
- [ ] Loading states display correctly
- [ ] Error messages are user-friendly
- [ ] App works with slow network connections
- [ ] App handles offline scenarios (shows errors)

### 8. Performance
- [ ] Videos load smoothly
- [ ] Scrolling is smooth
- [ ] No memory leaks during extended use
- [ ] App doesn't crash during normal usage

## Common Issues and Solutions

### Issue: "Network request failed" or API errors
**Solution:**
1. Verify API_BASE is set correctly: `echo $API_BASE`
2. Test API directly: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health`
3. Check if API is accessible from your network
4. For emulator, use `10.0.2.2` instead of `localhost`

### Issue: "Unable to resolve module" errors
**Solution:**
```bash
cd apps/mobile
rm -rf node_modules
npm install
npx expo start --clear
```

### Issue: App doesn't load on physical device
**Solution:**
1. Ensure phone and computer are on same WiFi
2. Check firewall settings on your computer
3. Try using tunnel mode: `npx expo start --tunnel`
4. Verify Expo Go app is up to date

### Issue: Videos don't play
**Solution:**
1. Check if YouTube video IDs are valid
2. Verify API is returning video data: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?limit=1`
3. Check console for errors in Expo CLI
4. Ensure `react-native-youtube-iframe` is properly installed

### Issue: Google Sign-In doesn't work
**Solution:**
1. This is expected if OAuth credentials aren't configured
2. Use email sign-in instead (works without setup)
3. To enable Google Sign-In, set up OAuth credentials in Google Cloud Console

### Issue: App crashes on startup
**Solution:**
1. Clear cache: `npx expo start --clear`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check Expo SDK version matches: Should be 54.0.0
4. Check for TypeScript errors: `npx tsc --noEmit`

## Debugging Tips

### 1. View Logs
- Expo CLI shows console.log output
- Use React Native Debugger for advanced debugging
- Enable remote debugging in Expo Go app

### 2. Check API Calls
- Open Expo CLI console to see API requests
- Check Network tab in React Native Debugger
- Verify API responses in terminal logs

### 3. Test API Independently
```bash
# Test health endpoint
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health

# Test content endpoint
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?limit=5

# Test categories endpoint
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/categories
```

### 4. Clear Cache
```bash
# Clear Expo cache
npx expo start --clear

# Clear Metro bundler cache
rm -rf .expo
rm -rf node_modules/.cache
```

## Testing on Different Platforms

### Android
- Best experience on physical device
- Emulator works but may be slower
- Test on different screen sizes
- Test on Android 8.0+ (API level 26+)

### iOS
- Requires macOS and Xcode
- Test on different iPhone models
- Test on iPad (supports tablet)
- Test on iOS 13.0+

### Web
- Limited functionality (some native features won't work)
- Good for quick testing
- YouTube player may have limitations

## Performance Testing

### 1. Load Testing
- Test with slow network (throttle in dev tools)
- Test with many videos loaded
- Test infinite scroll with large datasets

### 2. Memory Testing
- Monitor memory usage during extended use
- Test with many videos in swipe player
- Check for memory leaks

### 3. Battery Testing
- Monitor battery usage during video playback
- Test background behavior
- Test app state management

## Next Steps After Testing

1. **Fix any bugs found** during testing
2. **Optimize performance** based on test results
3. **Add error handling** for edge cases
4. **Improve UI/UX** based on user feedback
5. **Add analytics** to track usage
6. **Set up CI/CD** for automated testing
7. **Prepare for production** build

## Production Build

When ready for production:

```bash
# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios

# Configure EAS (Expo Application Services)
eas init
```

## Additional Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Navigation](https://reactnavigation.org/)
- [React Native YouTube IFrame](https://github.com/LonelyCpp/react-native-youtube-iframe)
- [Expo Auth Session](https://docs.expo.dev/guides/authentication/#google)

## Support

If you encounter issues:
1. Check Expo CLI logs
2. Check API server status
3. Verify environment variables
4. Check network connectivity
5. Review error messages in app

