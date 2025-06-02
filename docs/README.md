# Project Documentation

Welcome to the documentation for the Vulnerability SDK System project. This documentation provides comprehensive guides and references for all components of the system.

## Table of Contents

- [SDK Usage](#sdk-usage)
- [API Endpoints](#api-endpoints)
- [Portal Usage](#portal-usage)
- [Example App Usage](#example-app-usage)
- [Setup Instructions](#setup-instructions)
- [Diagrams & Screenshots](#diagrams--screenshots)

---

## SDK Usage

The Vulnerability SDK allows you to easily integrate code scanning and vulnerability management into your Android applications.

### 1. Add the SDK to Your Project

If using as a module, add the SDK module to your `settings.gradle` and `build.gradle` files.

### 2. Initialize the Controller
```java
VulnerabilitiesController controller = new VulnerabilitiesController();
```

### 3. Register a New User
```java
controller.register("username", "password", new VulnerabilitiesController.Callback<AuthResponse>() {
    @Override
    public void onSuccess(AuthResponse response) {
        // Handle successful registration
    }
    @Override
    public void onError(String error) {
        // Handle error
    }
});
```

### 4. Scan Code
```java
controller.scanCode(token, code, language, new VulnerabilitiesController.Callback<ScanResponse>() {
    @Override
    public void onSuccess(ScanResponse response) {
        // Handle scan results
    }
    @Override
    public void onError(String error) {
        // Handle error
    }
});
```

### 5. Fetch Scan History
```java
controller.getScanHistory(token, new VulnerabilitiesController.Callback<ScanHistoryResponse>() {
    @Override
    public void onSuccess(ScanHistoryResponse response) {
        // Handle scan history
    }
    @Override
    public void onError(String error) {
        // Handle error
    }
});
```

### 6. Fetch Scan Details
```java
controller.getScanDetails(token, scanId, new VulnerabilitiesController.Callback<ScanResponse>() {
    @Override
    public void onSuccess(ScanResponse response) {
        // Handle scan details
    }
    @Override
    public void onError(String error) {
        // Handle error
    }
});
```

### 7. Delete a Scan
```java
controller.deleteScan(token, scanId, new VulnerabilitiesController.Callback<DeleteResponse>() {
    @Override
    public void onSuccess(DeleteResponse response) {
        // Handle successful deletion
    }
    @Override
    public void onError(String error) {
        // Handle error
    }
});
```

---

## API Endpoints

Below are the main backend API endpoints provided by the system:

| Method | Path                | Headers            | Body / Params         | Description                       |
|--------|---------------------|--------------------|-----------------------|-----------------------------------|
| POST   | /api/auth/register  | -                  | username, password    | Register a new user               |
| POST   | /api/scan           | Authorization      | code, language        | Scan code for vulnerabilities     |
| GET    | /api/scans          | Authorization      | -                     | Get scan history for user         |
| GET    | /api/scans/{scanId} | Authorization      | -                     | Get details for a specific scan   |
| DELETE | /api/scans/{scanId} | Authorization      | -                     | Delete a scan by ID               |

### Example: Register
```json
POST /api/auth/register
{
  "username": "user1",
  "password": "pass123"
}
```

### Example: Scan Code
```json
POST /api/scan
Headers: { "Authorization": "<token>" }
{
  "code": "print('hello')",
  "language": "python"
}
```

### Example: Get Scan History
```
GET /api/scans
Headers: { "Authorization": "<token>" }
```

### Example: Get Scan Details
```
GET /api/scans/{scanId}
Headers: { "Authorization": "<token>" }
```

### Example: Delete Scan
```
DELETE /api/scans/{scanId}
Headers: { "Authorization": "<token>" }
```

---

## Example App Usage

The Android Example Application demonstrates how to integrate and use the Vulnerability SDK in a real-world scenario.

### Features Demonstrated
- User registration and authentication
- Submitting code for vulnerability scanning
- Viewing scan history and details
- Deleting scans

### How to Run
1. Open the example app project in Android Studio.
2. Make sure the backend API is running locally.
3. Build and run the app on an emulator or device.

### How to Use
- Register or log in with your credentials.
- Use the provided UI to submit code for scanning.
- Browse your scan history and tap on any scan to view details.
- Delete scans as needed.

This app is a reference for developers on how to use the SDK in their own projects.

---

## Setup Instructions

Follow these steps to set up and run each component locally:

### Prerequisites
- Java 8+ and Android Studio (for SDK and example app)
- Python 3.8+ (for backend)
- Node.js 16+ and npm (for portal)

### 1. Backend (Flask API)
```bash
cd backend-api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python init_db.py  # Initialize the database
python app.py      # Start the backend server (default: http://localhost:5000)
```

### 2. Android SDK
- Open the `app` module in Android Studio.
- Build the project to generate the SDK.
- (Optional) Publish to a repository for integration.

### 3. Portal (Frontend)
```bash
cd frontend
npm install
npm run dev  # Runs the portal at http://localhost:3000
```

### 4. Example App
- (If available) Open the example app in Android Studio and run on an emulator or device.

---

## Diagrams & Screenshots

Visual aids help understand the system architecture and user flows.

### Architecture Diagram
- Add a diagram showing the relationship between the backend API, SDK, portal, and example app.
- Recommended tools: draw.io, Lucidchart, or simple PNG/JPG images.

### Portal Screenshots
- Add screenshots of the login page, dashboard, scan history, and scan details views.

### Example App Screenshots
- Add screenshots of the registration, scan submission, scan history, and scan details screens.

> To add images, place them in the `docs/images/` folder and reference them here:
> `![Description](images/your-image.png)`

--- 