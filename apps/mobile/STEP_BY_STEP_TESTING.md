# Step-by-Step Testing Guide - Lumens Mobile App

## Prerequisites Check

### Step 1: Verify Node.js Installation
```bash
node --version
```
**Expected**: v18 or higher (you have v20.19.5 ✅)

```bash
npm --version
```
**Expected**: Any recent version (you have 10.8.2 ✅)

### Step 2: Choose Your Testing Method

**Option A: Physical Device (Recommended - Easiest)**
- Install Expo Go app on your phone
- iOS: [Download from App Store](https://apps.apple.com/app/expo-go/id982107779)
- Android: [Download from Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

**Option B: Android Emulator**
- Install Android Studio: https://developer.android.com/studio
- Create an Android Virtual Device (AVD)
- Start the emulator before testing

**Option C: iOS Simulator (macOS only)**
- Install Xcode from App Store
- iOS Simulator comes with Xcode

---

## Installation Steps

### Step 3: Navigate to Mobile App Directory
```bash
cd /Users/nayeem/vscode_repos/lumens/apps/mobile
```

### Step 4: Install Dependencies
```bash
npm install
```

**Expected output**: Dependencies will be installed. This may take 2-3 minutes.

**If you see errors**: 
- Make sure you're in the correct directory
- Try: `rm -rf node_modules package-lock.json && npm install`

### Step 5: Verify API Configuration
```bash
cat app.config.js | grep apiBase
```

**Expected**: Should show the API URL: `https://lumens-api-4qubw3p5lq-uc.a.run.app`

---

## Running the App

### Step 6: Start the Development Server

**Method 1: Using the start script (Easiest)**
```bash
./start.sh
```

**Method 2: Manual start**
```bash
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
npx expo start
```

**Expected output**: 
- Metro bundler starts
- QR code appears in terminal
- Options menu appears with keys to press

### Step 7: Choose Your Platform

**For Physical Device:**
1. Open Expo Go app on your phone
2. Scan the QR code displayed in terminal
3. Wait for app to load (first time may take 1-2 minutes)

**For Android Emulator:**
- Press `a` in the terminal
- Wait for emulator to open and app to load

**For iOS Simulator (macOS only):**
- Press `i` in the terminal
- Wait for simulator to open and app to load

**For Web Browser:**
- Press `w` in the terminal
- App opens in browser (limited functionality)

---

## Testing Steps

### Step 8: Test Login Screen

**What to test:**
1. ✅ App opens and shows login screen
2. ✅ Email input field is visible
3. ✅ "Continue" button is visible
4. ✅ "Continue with Google" button is visible (may not work without OAuth setup)

**How to test:**
1. Enter any email address (e.g., `test@example.com`)
2. Click "Continue" button
3. **Expected**: App navigates to Latest screen

**If login fails:**
- Check terminal for error messages
- Verify API is accessible: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health`

### Step 9: Test Latest Screen

**What to test:**
1. ✅ Videos load from API
2. ✅ Featured video player displays at top
3. ✅ Video grid shows below featured player
4. ✅ User email displays at top
5. ✅ Sign out button works

**How to test:**
1. Wait for videos to load (loading indicator appears first)
2. **Expected**: Featured video player shows at top
3. **Expected**: Grid of video thumbnails below
4. Scroll down to see more videos
5. **Expected**: More videos load automatically (infinite scroll)
6. Tap on a video thumbnail
7. **Expected**: Featured player updates to show selected video
8. Tap "Sign out" button
9. **Expected**: Returns to login screen

**If videos don't load:**
- Check terminal for API errors
- Verify API is accessible: `curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?limit=5`
- Check network connection

### Step 10: Test Categories Screen

**What to test:**
1. ✅ Categories load from API
2. ✅ Category list displays
3. ✅ Can navigate to feed screen

**How to test:**
1. Navigate to Categories screen (if accessible from Latest screen)
2. **Expected**: List of categories appears:
   - Prophets
   - Duas & Supplications
   - Ramadan
   - Seerah
   - Nasheeds
3. Tap on a category
4. **Expected**: Navigates to Feed screen with videos for that topic

**Note**: If Categories screen is not accessible from Latest screen, you may need to add navigation or test it separately.

### Step 11: Test Feed Screen

**What to test:**
1. ✅ Videos load for selected topic
2. ✅ Grid layout displays correctly
3. ✅ Thumbnails load and display
4. ✅ Video titles and channel names show
5. ✅ Infinite scroll works
6. ✅ Can navigate to Swipe Player

**How to test:**
1. From Categories, tap a category (or navigate to Feed screen)
2. **Expected**: Videos for that topic load
3. **Expected**: 2-column grid layout
4. Scroll down
5. **Expected**: More videos load automatically
6. Tap on a video
7. **Expected**: Navigates to Swipe Player screen

**If feed doesn't load:**
- Check terminal for API errors
- Verify topic parameter is being sent correctly
- Test API directly: `curl "https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?topic=prophets&limit=5"`

### Step 12: Test Swipe Player Screen

**What to test:**
1. ✅ Videos load for the topic
2. ✅ Video player displays correctly
3. ✅ Can swipe horizontally between videos
4. ✅ Only visible video plays
5. ✅ Videos autoplay when scrolled into view
6. ✅ Infinite scroll loads more videos

**How to test:**
1. From Feed screen, tap a video
2. **Expected**: Swipe Player opens with video playing
3. Swipe left or right (or scroll horizontally)
4. **Expected**: Next/previous video appears
5. **Expected**: Only the visible video plays
6. Continue swiping through videos
7. **Expected**: More videos load as you reach the end
8. **Expected**: Smooth scrolling and playback

**If swipe player doesn't work:**
- Check terminal for errors
- Verify video IDs are being extracted correctly
- Check YouTube player is loading
- Test with different videos

### Step 13: Test Video Playback

**What to test:**
1. ✅ Videos play correctly
2. ✅ Play/pause controls work
3. ✅ Video quality is acceptable
4. ✅ Videos load smoothly

**How to test:**
1. Open a video in Swipe Player or Latest screen
2. **Expected**: Video starts playing (or is ready to play)
3. Tap on video player
4. **Expected**: Play/pause controls appear
5. **Expected**: Video plays smoothly
6. Test multiple videos
7. **Expected**: All videos play correctly

**If videos don't play:**
- Check YouTube video IDs are valid
- Verify API is returning video data
- Check network connection
- Test YouTube URLs directly in browser

### Step 14: Test Error Handling

**What to test:**
1. ✅ App handles API errors gracefully
2. ✅ Error messages display correctly
3. ✅ App doesn't crash on errors

**How to test:**
1. Turn off WiFi/mobile data temporarily
2. Try to load videos
3. **Expected**: Error message appears (not a crash)
4. Turn WiFi/mobile data back on
5. **Expected**: Videos load successfully

**If app crashes:**
- Check terminal for error stack traces
- Verify error handling is implemented
- Check for null/undefined values

### Step 15: Test Navigation

**What to test:**
1. ✅ Can navigate between screens
2. ✅ Back button works
3. ✅ Navigation is smooth
4. ✅ State is preserved

**How to test:**
1. Navigate through all screens:
   - Login → Latest → Categories → Feed → Swipe Player
2. Use back button to go back
3. **Expected**: Navigation works smoothly
4. **Expected**: Previous screen state is preserved
5. Test going back multiple screens
6. **Expected**: Navigation stack works correctly

---

## Troubleshooting

### Problem: "Network request failed"
**Solution:**
```bash
# Test API directly
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health

# Check API_BASE is set
echo $API_BASE

# For Android emulator, use:
export API_BASE=http://10.0.2.2:8000  # If testing with local API
```

### Problem: "Unable to resolve module"
**Solution:**
```bash
cd apps/mobile
rm -rf node_modules
npm install
npx expo start --clear
```

### Problem: App doesn't load on phone
**Solution:**
1. Ensure phone and computer are on same WiFi
2. Try tunnel mode: `npx expo start --tunnel`
3. Check firewall settings
4. Verify Expo Go app is up to date

### Problem: Videos don't play
**Solution:**
1. Check API is returning video data:
   ```bash
   curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?limit=1
   ```
2. Verify YouTube video IDs are valid
3. Check console for errors in terminal
4. Test YouTube URLs directly in browser

### Problem: App crashes on startup
**Solution:**
```bash
# Clear cache
npx expo start --clear

# Reinstall dependencies
rm -rf node_modules
npm install

# Check for TypeScript errors
npx tsc --noEmit
```

---

## Testing Checklist

Use this checklist to track your testing progress:

### Authentication
- [ ] Login screen displays correctly
- [ ] Email sign-in works
- [ ] Google sign-in button visible (may not work without OAuth)
- [ ] Sign out works
- [ ] User email displays correctly

### Latest Screen
- [ ] Videos load from API
- [ ] Featured video player displays
- [ ] Video grid displays correctly
- [ ] Infinite scroll works
- [ ] Video selection updates featured player
- [ ] Loading indicators show correctly
- [ ] Error messages display correctly

### Categories Screen
- [ ] Categories load from API
- [ ] Category list displays
- [ ] Can navigate to feed screen
- [ ] Navigation works correctly

### Feed Screen
- [ ] Videos load for topic
- [ ] Grid layout displays correctly
- [ ] Thumbnails load
- [ ] Video titles and channels display
- [ ] Infinite scroll works
- [ ] Can navigate to swipe player
- [ ] Loading states work
- [ ] Error handling works

### Swipe Player Screen
- [ ] Videos load for topic
- [ ] Video player displays
- [ ] Horizontal scrolling works
- [ ] Only visible video plays
- [ ] Videos autoplay correctly
- [ ] Infinite scroll works
- [ ] Smooth scrolling
- [ ] Loading states work

### Video Playback
- [ ] Videos play correctly
- [ ] Play/pause controls work
- [ ] Video quality is acceptable
- [ ] Videos load smoothly
- [ ] Multiple videos play correctly

### Error Handling
- [ ] API errors handled gracefully
- [ ] Error messages display
- [ ] App doesn't crash on errors
- [ ] Network errors handled

### Navigation
- [ ] Can navigate between screens
- [ ] Back button works
- [ ] Navigation is smooth
- [ ] State is preserved

### Performance
- [ ] App loads quickly
- [ ] Videos load smoothly
- [ ] Scrolling is smooth
- [ ] No memory leaks
- [ ] App doesn't slow down over time

---

## Quick Reference Commands

### Start the app
```bash
cd apps/mobile
./start.sh
# Or: npx expo start
```

### Test API
```bash
# Health check
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/health

# Get videos
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?limit=5

# Get categories
curl https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/categories
```

### Clear cache
```bash
npx expo start --clear
```

### Reinstall dependencies
```bash
rm -rf node_modules
npm install
```

### Check for errors
```bash
npx tsc --noEmit
```

---

## Success Criteria

Your testing is successful if:
- ✅ App starts without errors
- ✅ Login works
- ✅ Videos load and display
- ✅ Navigation works smoothly
- ✅ Video playback works
- ✅ Infinite scroll works
- ✅ Error handling works
- ✅ No crashes during normal use

---

## Next Steps After Testing

1. **Document any bugs** you find
2. **Note any performance issues**
3. **Suggest improvements** for UI/UX
4. **Test on different devices** if possible
5. **Test with different network conditions**
6. **Verify all features work as expected**

---

## Need Help?

1. Check terminal logs for errors
2. Verify API is accessible
3. Check network connectivity
4. Review error messages in app
5. Check Expo documentation: https://docs.expo.dev/
6. Check React Navigation documentation: https://reactnavigation.org/

---

## Summary

**Quick Start:**
1. `cd apps/mobile`
2. `npm install`
3. `./start.sh`
4. Scan QR code with Expo Go or press 'a' for Android

**Testing Order:**
1. Login → 2. Latest Screen → 3. Categories → 4. Feed → 5. Swipe Player → 6. Video Playback

**Expected Time:** 15-30 minutes for full testing

**Ready to test?** Follow the steps above and check off items in the testing checklist!

