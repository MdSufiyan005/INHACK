# Deployment Guide for INHACK on Render

This guide provides step-by-step instructions for deploying the INHACK application on Render with Redis from Redis.com.

## Prerequisites

1. A Render account (https://render.com)
2. A Redis.com account with a Redis instance
3. All required API keys (Twilio, Groq, Google Cloud Vision)

## Step 1: Prepare Your Redis Instance on Redis.com

1. Sign up or log in to Redis.com
2. Create a new Redis database
3. Note down the following connection details:
   - Host
   - Port
   - Password
   - Connection string

## Step 2: Configure Environment Variables

Update the following environment variables in your `render.yaml` file or Render dashboard:

```yaml
envVars:
  # Redis connection (from Redis.com)
  - key: CELERY_BROKER_URL
    value: redis://default:<password>@<host>:<port>
  - key: CELERY_RESULT_BACKEND
    value: redis://default:<password>@<host>:<port>
  
  # Database URL (you can use Render's built-in PostgreSQL or your own)
  - key: DATABASE_URL
    value: your-database-url
  
  # API Keys
  - key: TWILIO_SID
    value: your-twilio-sid
  - key: TWILIO_AUTH_TOKEN
    value: your-twilio-auth-token
  - key: GROQ_API_KEY
    value: your-groq-api-key
  - key: GOOGLE_APPLICATION_CREDENTIALS
    value: your-google-credentials
  
  # Application Settings
  - key: ALLOWED_ORIGINS
    value: https://your-render-app-url.onrender.com
  - key: TIMEZONE
    value: Asia/Kolkata
```

## Step 3: Deploy to Render

1. Fork the repository to your GitHub account
2. Log in to Render dashboard
3. Click "New Web Service"
4. Connect your GitHub account
5. Select your forked repository
6. Configure the service:
   - Name: inhack
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `sh -c 'uvicorn main:app --host 0.0.0.0 --port $PORT & celery -A core.celery worker --loglevel=info'`
   - Instance Type: Free or Starter (based on your needs)

7. Add environment variables from Step 2
8. Click "Create Web Service"

## Step 4: Configure Auto-Deployment (Optional)

1. In your Render dashboard, go to your web service
2. Click on "Settings" tab
3. Scroll to "Auto-Deploy"
4. Select "Yes" to enable auto-deployment on GitHub pushes

## Step 5: Monitor Deployment

1. Check the logs in Render dashboard for any errors
2. Ensure both FastAPI and Celery processes start correctly
3. Test the application by accessing your Render URL

## Troubleshooting

### Common Issues

1. **Celery not connecting to Redis**:
   - Verify your Redis connection string
   - Check if Redis instance is active
   - Ensure correct password and host details

2. **Database connection errors**:
   - Verify DATABASE_URL is correctly set
   - Check if database is accessible

3. **Missing environment variables**:
   - Ensure all required API keys are set
   - Check for typos in variable names

### Logs

You can view logs in Render dashboard:
1. Go to your web service
2. Click on "Logs" tab
3. Check for any error messages

## Scaling Considerations

For production use:

1. Consider separating FastAPI and Celery into different services
2. Use a more robust database solution
3. Implement proper monitoring and alerting
4. Set up custom domains
5. Configure SSL certificates

## Updating the Application

To update your deployed application:

1. Push changes to your GitHub repository
2. If auto-deployment is enabled, Render will automatically deploy
3. If not, manually trigger deployment from Render dashboard

## Cost Considerations

- Render's free tier includes:
  - 512 MB RAM
  - 10 GB disk space
  - 15 minutes of build time per day
  - 750 hours of instance runtime per month

- For production use, consider upgrading to a paid plan

## Support

For issues with deployment:
1. Check Render's documentation: https://render.com/docs
2. Review application logs
3. Verify all environment variables are correctly set
4. Contact Render support if needed
