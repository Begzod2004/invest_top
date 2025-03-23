# Top Invest Backend

This is the backend for the Top Invest application, configured for deployment on Timeweb Cloud with SQLite database.

## Version Compatibility

Important version requirements:

- Django 4.2.10 (not 5.x)
- django-jazzmin 2.4.0

Using Django 5.x with the current version of django-jazzmin causes template errors with the `length_is` filter.

## Deployment Instructions for Timeweb Cloud

### Prerequisites

- A Timeweb Cloud account
- Docker installed on your local machine (for building the image)

### Steps to Deploy

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd top-invest-1/backend
   ```

2. **Update the .env file**

   - Edit the `.env` file and update the following:
     - `SECRET_KEY`: Set a secure secret key
     - `ALLOWED_HOSTS`: Add your Timeweb Cloud domain
     - `CORS_ALLOWED_ORIGINS`: Add your frontend domain
     - `BOT_TOKEN`: Your Telegram bot token
     - `CHANNEL_ID`: Your Telegram channel ID

3. **Build and push the Docker image**

   ```bash
   docker build -t top-invest-backend .
   ```

4. **Deploy to Timeweb Cloud**

   - Log in to your Timeweb Cloud account
   - Create a new Docker container
   - Select the Docker image you pushed
   - Set the following environment variables:
     - All variables from your `.env` file
   - Map port 8000 to the external port
   - Add persistent volumes for:
     - `/app/db.sqlite3`
     - `/app/media`
     - `/app/payment_screenshots`

5. **Access your application**
   - Your backend will be available at `https://your-domain.timeweb.cloud`
   - Admin panel: `https://your-domain.timeweb.cloud/admin/`
   - API documentation: `https://your-domain.timeweb.cloud/swagger/`

## Local Development

1. **Set up the environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run migrations**

   ```bash
   python manage.py migrate
   ```

3. **Create a superuser**

   ```bash
   python manage.py createsuperuser
   ```

4. **Run the development server**

   ```bash
   python manage.py runserver
   ```

5. **Using Docker Compose**
   ```bash
   docker-compose up --build
   ```

## Project Structure

- `config/`: Django project settings
- `users/`: User management app
- `signals/`: Trading signals app
- `subscriptions/`: Subscription management app
- `payments/`: Payment processing app
- `instruments/`: Trading instruments app
- `reviews/`: User reviews app
- `dashboard/`: Admin dashboard app
- `invest_bot/`: Telegram bot integration
