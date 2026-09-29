# Setu for iPhone and Android

The apps wrap the same Setu web app (`../index.html`) with [Capacitor](https://capacitorjs.com), and add native features:

- **Private storage** mirrored to the phone's secure app storage, so data survives the system clearing web storage
- **Face ID / fingerprint lock** (Settings → Lock with Face ID or fingerprint)
- **Monthly reminders** on pay day and for backups (Settings → Monthly reminders)
- **Share sheet** for backups and CSV exports
- **Haptics**, native status bar and splash screen, Android back button, links open in an in-app browser
- No analytics, no service worker, no tip jar (app stores require their own payment systems for tips)

App ID: `io.github.myselfsislam.setu` (can't be changed after the first release).

## Build

You need a **Mac with Xcode 16+** for iOS, and **Android Studio** (any OS) for Android.

```bash
cd app
npm install
npm run sync          # copies ../index.html into the apps
npx cap open android  # Android Studio: Build → Generate Signed Bundle (AAB)
npx cap open ios      # Xcode: pick your team, then Product → Archive
```
On a Mac, the first `npm run sync` also runs `pod install` (install CocoaPods with `brew install cocoapods` if needed).

After **any** change to `../index.html`, run `npm run sync` again, raise the version (Android: `versionCode`/`versionName` in `android/app/build.gradle`; iOS: Version/Build in Xcode), and upload a new build.

Icons and launch screens come from `resources/`. To regenerate: `npm run assets`.

## Publish

See `STORE_LISTING.md` for the text, answers and screenshots to paste into App Store Connect and Google Play Console.
