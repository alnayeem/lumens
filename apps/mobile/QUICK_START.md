# Quick Start Guide - Lumens Mobile App

## 🚀 Fastest Way to Test

### Option 1: Using the Start Script (Recommended)
```bash
cd apps/mobile
./start.sh
```

### Option 2: Manual Start
```bash
cd apps/mobile
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
npm install  # First time only
npx expo start
```

## 📱 Testing on Your Phone (Easiest)

1. **Install Expo Go** on your phone:
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. **Start the app**:
   ```bash
   cd apps/mobile
   ./start.sh
   ```

3. **Scan the QR code**:
   - iOS: Use Camera app to scan QR code
   - Android: Use Expo Go app to scan QR code

4. **Wait for app to load** - First load may take a minute

## 💻 Testing on Emulator/Simulator

### Android Emulator
```bash
cd apps/mobile
./start.sh
# Then press 'a' in the terminal
```

### iOS Simulator (macOS only)
```bash
cd apps/mobile
./start.sh
# Then press 'i' in the terminal
```

### Web Browser
```bash
cd apps/mobile
./start.sh
# Then press 'w' in the terminal
```

## ✅ Quick Test Checklist

1. **Login Screen**
   - Enter any email (e.g., `test@example.com`)
   - Click "Continue"
   - Should navigate to Latest screen

2. **Latest Screen**
   - Should see videos loading
   - Featured video player at top
   - Video grid below
   - Scroll to load more videos

3. **Categories**
   - Navigate to Categories (if accessible)
   - Should see topic list
   - Tap a category to see videos

4. **Swipe Player**
   - Tap a video from Latest or Feed
   - Should open swipe player
   - Swipe horizontally to see more videos
   - Only visible video should play

## 🔧 Troubleshooting

### "Network request failed"
- Check API_BASE is set: `echo $API_BASE`
- Test API: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health`
- Ensure phone and computer are on same WiFi

### "Unable to resolve module"
```bash
cd apps/mobile
rm -rf node_modules
npm install
npx expo start --clear
```

### App doesn't load on phone
- Ensure phone and computer are on same WiFi
- Try tunnel mode: `npx expo start --tunnel`
- Check Expo Go app is up to date

### Videos don't play
- Check API is returning data
- Verify YouTube video IDs are valid
- Check console for errors

## 📊 Current Status

✅ **Ready to Test**
- API configured: `https://lumens-api-4qubw3p5lq-uc.a.run.app`
- Dependencies: Ready to install
- Code: No errors, ready to run
- Configuration: Default API URL set

## 🎯 What to Test

1. **Authentication**: Email sign-in works
2. **Video Loading**: Videos load from API
3. **Navigation**: Can navigate between screens
4. **Video Playback**: Videos play correctly
5. **Infinite Scroll**: More videos load on scroll
6. **Error Handling**: Errors display correctly

## 📚 More Information

- **Full Testing Guide**: See [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **App Assessment**: See [MOBILE_APP_ASSESSMENT.md](./MOBILE_APP_ASSESSMENT.md)
- **API Documentation**: See [../../README.md](../../README.md)

## 🆘 Need Help?

1. Check the [TESTING_GUIDE.md](./TESTING_GUIDE.md) for detailed instructions
2. Check Expo CLI logs for errors
3. Verify API is accessible: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health`
4. Check network connectivity
5. Review error messages in app

## 🎉 Ready to Go!

Your mobile app is ready to test. Just run:
```bash
cd apps/mobile
./start.sh
```

Then scan the QR code with Expo Go on your phone, or press 'a' for Android emulator, 'i' for iOS simulator, or 'w' for web browser.

