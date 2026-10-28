# FreshSense Android and iPhone apps

Both apps reuse the React food scanning, OCR, pantry, history, and workspace screens through Capacitor 8. The native projects are `frontend/android` and `frontend/ios/App/App.xcodeproj`. Their provisional application ID is `app.freshsense.mobile`; confirm ownership before the first store release.

The deployed site is https://freshsense-ai-nine.vercel.app. The Android test APK uses https://freshsense-ai-nine.vercel.app/api/v1 and is available locally at `releases/FreshSense-android.apk`. The hosted download is https://freshsense-ai-nine.vercel.app/downloads/FreshSense.apk. It is signed with the Android development key for direct installation, not a Play Store release. The iPhone project is prepared; iPhone distribution is deferred at the owner's request.

## Sessions

Browser requests use a same-origin `/api/v1` proxy and HttpOnly cookies. Login and registration confirm `/auth/me` before displaying success. The development launcher supports both `localhost` and `127.0.0.1` without mixing cookie hosts.

Native requests use Capacitor's native HTTP transport and a revocable bearer token. Tokens are stored in iOS Keychain or Android Keystore-encrypted storage, excluded from cloud keychain sync and cleared on logout. The API issues a native token only after verifying the registration/login credentials. Production browser responses still omit bearer tokens. Deploy the updated backend before using a native build.

## Build with a public backend

Run from `frontend`:

```sh
npm ci
MOBILE_API_URL=https://freshsense-ai-nine.vercel.app/api/v1 npm run mobile:sync
```

Use the real reachable HTTPS URL. `localhost` on a phone refers to that phone. Analysis requires a network connection; AI models remain on the server. Mobile builds disable the web service worker and include the built screens in the application.

### Android

Install Java 21, Android SDK platform 36 and build-tools 36, then:

```sh
cd android
./gradlew assembleDebug
```

The test APK is `app/build/outputs/apk/debug/app-debug.apk`. Use Android Studio's signed bundle workflow for a Play release; keep the signing key outside source control. Release builds reject cleartext HTTP.

For USB development, run the normal backend, forward its port with `adb reverse tcp:8000 tcp:8000`, then sync using `MOBILE_API_URL=http://localhost:8000/api/v1 MOBILE_ALLOW_HTTP=1 npm run mobile:sync android`. This produces a local test build, not a public release.

### iPhone

On a Mac with a Capacitor 8 supported Xcode, run `npm run mobile:sync` with the real API URL and `npm run mobile:ios`. Swift Package Manager resolves the native dependencies. Choose your Apple developer team, test on a device, then Archive and upload to TestFlight/App Store Connect. This Linux workspace can generate the iOS project but cannot compile or sign an iPhone binary.

Camera/photo usage descriptions are included. Test camera selection, photo uploads, protected image loading, session restoration, logout, and no-network errors on both physical platforms before distribution.

## Vercel

Deploy from the repository root using `vercel.json`. This builds the web client and FastAPI function together, keeping browser requests on the same origin. The build prepares the food-category embeddings. To fit Vercel's function size limit, the first image scan on each new server instance downloads the pinned CLIP image encoder into `/tmp`, verifies its SHA256, and caches it for subsequent scans. This first scan can take longer. RapidOCR includes its CPU models.

Production requires server-only `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production`, and the attached private Blob store's `BLOB_READ_WRITE_TOKEN`. Set `VITE_API_URL=/api/v1`; the database must already be migrated to the current Alembic revision. Never expose database or Blob credentials through a `VITE_` variable.

The Vercel entrypoint uses `/tmp/freshsense-uploads` for working files and persists normalized photos and originals in private Blob storage. Image requests still require scan ownership or workspace membership. Containers and ordinary local runs retain their existing local storage unless Blob credentials are configured. Existing local photos must be migrated separately before they can be served online; their database records do not upload the original files automatically.

After verifying the production health endpoint, browser signup/login/reload, image scanning, and private-image readback, use `https://YOUR_VERCEL_HOST/api/v1` for `MOBILE_API_URL`. Production must be accessible to app users without a Vercel team login. Preview deployments can remain protected.

## Publication requirements still requiring the app owner's input

Confirm the application ID, Apple/Google developer accounts and signing, reachable production API, privacy policy/support URLs, store privacy and data safety disclosures, and account/data deletion flow. The existing food freshness prototype also needs its evidence limitations retained in the store description. A generated native project is not evidence of a signed store submission or approval.
