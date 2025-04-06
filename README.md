# ReTech - Sustainable Electronics Marketplace

A Flask web application for buying and selling used electronics, promoting sustainability and eco-friendly practices.

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Firebase:
   - Create a new Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Generate a new private key from Project Settings > Service Accounts
   - Save the JSON file securely
   - Update the `.env` file with the path to your Firebase credentials:
   ```
   FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-credentials.json
   ```

3. Run the application:
```bash
python app.py
```

## Features

- **Shop Page**: Browse available electronics
- **Sell Page**: List your electronics for sale
- **Firebase Integration**: Real-time database for product listings
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Toggle between light and dark themes

## API Endpoints

- `GET /api/products`: Get all products
- `POST /api/products`: Add a new product
- `GET /api/products/<product_id>`: Get specific product details

## Tech Stack

- Flask
- Firebase (Firestore)
- TailwindCSS
- HTML/JavaScript
