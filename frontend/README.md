# ScholarAI - Your AI-Powered Research Assistant

This is a Next.js application that uses Genkit and Firebase to provide AI-powered research assistance. Users can submit research topics, and the application will generate summaries and podcasts based on the input.

## Getting Started

Follow these instructions to get the project set up and running on your local machine for development and testing purposes.

### 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Node.js**: Version 18.x or later. You can download it from [nodejs.org](https://nodejs.org/).
- **npm** (Node Package Manager): This comes bundled with Node.js.

### 2. Firebase Setup

This project uses Firebase for user authentication.

1.  **Create a Firebase Project**: If you don't already have one, go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.

2.  **Create a Web App**:
    - In your Firebase project, click the gear icon next to "Project Overview" and select **Project settings**.
    - In the "Your apps" section, click the web icon (`</>`) to create a new web app.
    - Follow the registration steps. When you see the Firebase SDK snippet, copy the `firebaseConfig` object.

3.  **Configure Environment Variables**:
    - In the root of this project, you should have a `.env` file.
    - Copy the values from the `firebaseConfig` object into your `.env` file like this:

    ```bash
    NEXT_PUBLIC_FIREBASE_API_KEY="YOUR_API_KEY"
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="YOUR_AUTH_DOMAIN"
    NEXT_PUBLIC_FIREBASE_PROJECT_ID="YOUR_PROJECT_ID"
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="YOUR_STORAGE_BUCKET"
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="YOUR_MESSAGING_SENDER_ID"
    NEXT_PUBLIC_FIREBASE_APP_ID="YOUR_APP_ID"
    ```
    - **Important**: Replace `"YOUR_API_KEY"`, etc., with your actual Firebase project credentials.

4.  **Authorize Local Domain**:
    - In the Firebase Console, go to **Authentication** from the left-hand menu.
    - Select the **Settings** tab.
    - Under "Authorized domains," click **Add domain** and enter `localhost`.

### 3. Install Dependencies

Open your terminal, navigate to the project directory, and run the following command to install all the required packages from `package.json`:

```bash
npm install
```

### 4. Run the Application

This project has two main parts: the Next.js frontend and the Genkit AI backend. You'll typically want to run both in separate terminal windows.

1.  **Start the Next.js Development Server**:
    This command starts the main web application.

    ```bash
    npm run dev
    ```

    Once it's running, you can open your browser and go to [http://localhost:9002](http://localhost:9002).

2.  **Start the Genkit Development Server (Optional)**:
    This command starts the Genkit server, which powers the AI flows. It also provides a UI to inspect and test your flows.

    ```bash
    npm run genkit:dev
    ```

    You can view the Genkit developer UI at [http://localhost:4000](http://localhost:4000). The Next.js app will communicate with this server automatically.
