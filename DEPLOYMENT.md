# Deployment Guide for Timeweb Cloud

This guide provides step-by-step instructions for deploying the Top Invest backend to Timeweb Cloud using Docker with SQLite database.

## Prerequisites

- A Timeweb Cloud account
- Docker installed on your local machine
- Git installed on your local machine

## Step 1: Prepare Your Project

1. Clone the repository and navigate to the backend directory:

   ```bash
   git clone <repository-url>
   cd top-invest-1/backend
   ```

2. Update the `.env` file with your production settings:

   ```
   # Django secret key
   SECRET_KEY=your-secure-secret-key

   # Debug mode
   DEBUG=False

   # Allowed hosts
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.timeweb.cloud

   # Database configuration
   DB_ENGINE=django.db.backends.sqlite3
   DB_NAME=db.sqlite3

   # Telegram Bot settings
   BOT_TOKEN=your-telegram-bot-token
   CHANNEL_ID=your-telegram-channel-id

   # CORS settings
   CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```

   Replace the placeholders with your actual values.

## Step 2: Build and Test Locally

1. Build the Docker image:

   ```bash
   docker build -t top-invest-backend .
   ```

2. Run the container locally to test:

   ```bash
   docker run -p 8000:8000 -v $(pwd)/db.sqlite3:/app/db.sqlite3 -v $(pwd)/media:/app/media -v $(pwd)/payment_screenshots:/app/payment_screenshots --env-file .env top-invest-backend
   ```

3. Visit `http://localhost:8000/admin/` to verify the application is working correctly.

## Step 3: Deploy to Timeweb Cloud

### Option 1: Using Docker Registry

1. Create a Docker registry on Timeweb Cloud or use Docker Hub.

2. Tag and push your Docker image:

   ```bash
   docker tag top-invest-backend your-registry/top-invest-backend:latest
   docker push your-registry/top-invest-backend:latest
   ```

3. In the Timeweb Cloud dashboard:
   - Create a new Docker container
   - Select your Docker image
   - Configure environment variables from your `.env` file
   - Map port 8000 to the external port
   - Set up persistent volumes for:
     - `/app/db.sqlite3`
     - `/app/media`
     - `/app/payment_screenshots`

### Option 2: Using Docker Compose on Timeweb Cloud

1. Upload your project files to Timeweb Cloud using SFTP or Git.

2. Connect to your Timeweb Cloud server via SSH.

3. Navigate to your project directory and run:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Step 4: Configure Domain and SSL

1. In the Timeweb Cloud dashboard, go to the "Domains" section.

2. Add your domain and point it to your Docker container's IP address.

3. Enable SSL certificate for your domain.

## Step 5: Create Admin User

1. Connect to your container via SSH or use the Timeweb Cloud console.

2. Run the following command to create a superuser:

   ```bash
   docker exec -it your-container-name python manage.py createsuperuser
   ```

3. Follow the prompts to create an admin user.

## Step 6: Verify Deployment

1. Visit your domain (e.g., `https://your-domain.timeweb.cloud/admin/`) to access the admin panel.

2. Log in with the superuser credentials you created.

3. Check the API documentation at `https://your-domain.timeweb.cloud/swagger/`.

## Maintenance and Updates

### Backing Up the Database

1. Connect to your Timeweb Cloud server via SSH.

2. Copy the SQLite database file:
   ```bash
   docker cp your-container-name:/app/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3
   ```

### Updating the Application

1. Make changes to your code locally.

2. Build a new Docker image:

   ```bash
   docker build -t top-invest-backend:new .
   ```

3. Push the new image to your registry.

4. Update the container on Timeweb Cloud to use the new image.

## Troubleshooting

### Application Not Starting

Check the container logs:

```bash
docker logs your-container-name
```

### Database Issues

If you need to reset migrations:

```bash
docker exec -it your-container-name python manage.py migrate --fake-initial
```

### Static Files Not Loading

Verify the STATIC_ROOT and STATICFILES_STORAGE settings in settings.py and ensure collectstatic is running during deployment.

## Security Considerations

1. Keep your `.env` file secure and never commit it to public repositories.

2. Regularly update your Django and other dependencies.

3. Set up regular database backups.

4. Consider setting up a firewall to restrict access to your server.
