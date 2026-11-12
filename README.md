# EESI Elevators & Escalators Operations Console

![Android](https://img.shields.io/badge/Platform-Android-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-2.2.10-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white)
![Compose](https://img.shields.io/badge/Jetpack_Compose-Material_3-4285F4?style=for-the-badge&logo=jetpackcompose&logoColor=white)
![Room](https://img.shields.io/badge/Local_Storage-Room_SQLite-FF6F00?style=for-the-badge&logo=sqlite&logoColor=white)
![Supabase](https://img.shields.io/badge/Cloud_Backend-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-Automated-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

Official operations console for **EESI Elevators and Escalators Services**. Built for field engineers, safety inspectors, and maintenance technicians to handle Daily Time Records (DTR), Preventive Maintenance Service (PMS) checklists, job dispatches, live GPS tagging, and company safety announcements.

---

## ✨ Features

- **⏱️ Daily Time Records (DTR)**:
  - Local persistence via **Room SQLite** (`DtrEntity`, `DtrDao`, `DtrRoomRepository`).
  - Automated clock-in / clock-out with elapsed work duration calculation.
  - GPS latitude, longitude, and site facility location tagging.
  - Print-ready and exportable DTR timesheet preview.
- **☁️ Supabase Cloud Synchronization**:
  - Bidirectional sync to Supabase PostgreSQL (`dtr_logs`, `pms_inspections`, `announcements`).
  - Offline-first: Full local functionality with automatic cloud sync when connected.
  - Row Level Security (RLS) policies protecting enterprise data.
- **📋 Preventive Maintenance Service (PMS)**:
  - Comprehensive checklists: Traction motor, hoist ropes, brake assemblies, door interlocks, car-top inspection, and pit safety buffers.
- **📅 Smart Schedule & Field Dispatch**:
  - Building site locations, service routes, assigned crews, and emergency callouts.
- **📱 Responsive & Multi-Platform Adaptive**:
  - Adaptive container bounds (`max = 840.dp`) for vertical phones (Android/iOS viewports), foldables, tablets, and desktop/PC screens.
  - Dark mode and high-density compact layout modes.

---

## 🛠️ Architecture & Tech Stack

- **UI Framework**: Jetpack Compose with Material Design 3 (M3)
- **Architecture**: MVVM (Model-View-ViewModel) + Repository Pattern
- **Concurrency**: Kotlin Coroutines & StateFlow / SharedFlow
- **Local Database**: Android Jetpack Room with Kotlin Symbol Processing (KSP)
- **Networking**: Retrofit 2 + OkHttp 4 + Moshi for Supabase PostgREST endpoints
- **Environment Management**: Secrets Gradle Plugin reading `.env` / `.env.example`

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/barnayjar14/eesi-elevators.git
cd eesi-elevators
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your Supabase credentials:
```properties
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 3. Initialize Supabase Database
1. Open your [Supabase Dashboard](https://app.supabase.com).
2. Go to the **SQL Editor** tab.
3. Copy and run the script from [`supabase/schema.sql`](./supabase/schema.sql).
   This creates:
   - `public.profiles`
   - `public.dtr_logs`
   - `public.pms_inspections`
   - `public.service_schedules`
   - `public.incidents`
   - `public.announcements`
   - Enables Row Level Security (RLS) & Realtime replication.

### 4. Build and Run the App
To compile the debug APK:
```bash
./gradlew assembleDebug
```
To run the full test suite:
```bash
./gradlew testDebugUnitTest
```

---

## 🧪 Testing Suite

The repository includes comprehensive automated tests under `app/src/test/java/com/example/`:
- `DtrRoomTest.kt`: Unit tests verifying Room SQLite DAO operations, clock-in/out transitions, and location search.
- `EesiOperationsUnitTest.kt`: Unit tests for operational data models, PMS inspection status, and priority tags.
- `EesiRobolectricTest.kt`: Robolectric JVM tests verifying UI flow, authentication, and dispatch states without an emulator.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
