# Sheba - Service Marketplace

Sheba is a comprehensive full-stack web application designed to bridge the gap between local service providers and customers. Whether you need an electrician, a plumber, or a salon appointment, Sheba connects you with trusted professionals in your area.

The platform empowers users with real-time communication, location-based service matching, and intuitive dashboards for both customers and providers.

## \u2728 Key Features

- **Smart Matching**: Automatically finds providers based on category and proximity.
- **Real-Time Chat**: Integrated Socket.IO messaging for seamless communication between users and providers.
- **Role-Based Experience**: Dedicated dashboards for Users (to manage requests) and Providers (to manage jobs and earnings).
- **Dynamic Pricing**: Providers can set their own service fee ranges.
- **Interactive Map**: Location-based services using flexible radius matching.

## \uD83D\uDEE0\uFE0F Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Real-time**: Flask-SocketIO
- **Authentication**: JWT & Session-based Auth

### Frontend
- **Framework**: React.js (Vite)
- **Styling**: Styled Components & CSS Modules
- **HTTP Client**: Axios

## \uD83D\uDE80 Getting Started

Follow these steps to set up the project locally.

### Prerequisites
- Python 3.8+
- Node.js & npm
- PostgreSQL

### 1. Backend Setup

The backend runs on port `1588`.

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure Database
# Ensure you have a 'config.py' or .env with your DB credentials
# Then initialize the database:
flask db upgrade

# Run the server
python manage.py run
```
*Backend URL: `http://localhost:1588`*

### 2. Frontend Setup

The frontend runs on port `3000`.

```powershell
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*Frontend URL: `http://localhost:3000`*

## \uD83D\uDCC2 Project Structure

```
sheba/
├── backend/           # Flask API, Models, and Socket logic
│   ├── app/           # Application factory and blueprints
│   ├── migrations/    # Database migration scripts
│   └── manage.py      # Entry point for the application
├── frontend/          # React frontend application
│   ├── src/           # Components, Services, and Assets
│   └── vite.config.js # Vite configuration
└── README.md          # Project documentation
```

## \uD83E\uDD1D Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
*Built with \u2764\uFE0F for CSE471*
