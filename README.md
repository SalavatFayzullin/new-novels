# Flask Authentication Application

A simple Flask application with user authentication functionality. Users can register, log in, and access a protected main page after authentication.

## Features

- User registration with email and password
- User login with remember me functionality
- Protected routes that require authentication
- Redirects to main page after successful login
- SQLite database for user storage
- Password hashing for security

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Register a new account and log in to access the protected main page.

## Project Structure

- `app.py`: Main application file with routes and database models
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS)
- `instance/`: Contains the SQLite database file (created automatically)

## Technologies Used

- Flask: Web framework
- Flask-Login: User session management
- Flask-SQLAlchemy: Database ORM
- Werkzeug: Password hashing
- Bootstrap 5: Front-end styling 