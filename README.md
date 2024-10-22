# Finance Project

This project is a Django web application for financial backtesting and stock price predictions using linear regression model. It includes functionalities like backtesting strategies and generating performance reports with both graphical and tabular data.

## Features

- Financial backtesting with historical stock data.
- Prediction of stock prices using machine learning.
- Report generation including key financial metrics and visual comparisons.
- Dockerized setup for easy development and deployment.

## Prerequisites

Before running the project locally, ensure you have the following installed:

- **Docker** and **Docker Compose**
- **Python 3.10+**
- **Git** (for version control)

## Project Setup

### 1. Clone the repository
```bash
git clone <url-du-repository>
cd finance_project
```

### 2. Create and configure environment variables
Create a `.env` file at the root of your project to store environment variables, including your database credentials and API keys. Here's an example of what the `.env` file should look like:
```bash
POSTGRES_DB=finance_db
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

API_KEY=your_api_key_here
DEBUG=True
SECRET_KEY=your_secret_key_here

```
Make sure to replace `your_db_user`, `your_db_password`, and `your_api_key_here` with your actual credentials and API key. You can find your API key on [alphavantage](https://www.alphavantage.co/documentation/)


### 3. Install Docker and Docker Compose
Make sure Docker and Docker Compose are installed on your machine. If not, install them:

- [Docker Installation Guide](https://docs.docker.com/get-docker/)
- [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

### 4. Build and run the project
Run the following commands to start the application in a Dockerized environment:
```bash
docker-compose up --build
```
This will build the Docker images and start the services defined in the `docker-compose.yml` file.

### 5. Apply migrations and create superuser
Once the containers are up and running, you need to apply the database migrations:
```bash
docker-compose exec web python manage.py migrate
```
To create a superuser (for Django admin access), run:
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Access the application
You can access the Django application in your browser at:
```bash
http://localhost:8000
```

### 7. Running Tests
To run the tests included in the project, use the following command:
```bash
docker-compose exec web python manage.py test
```

## API Endpoints
The application provides several API endpoints for backtesting and predictions:

- `GET /backtesting?symbol=<SYMBOL>`: Runs the backtest for the given stock symbol.
- `GET /predict-stock/<SYMBOL>/`: Predicts stock prices for the next 30 days for the given symbol.
- `GET /report/<SYMBOL>/?format=pdf`: Generates a performance report in PDF format.

## Local Development : 
If you want to run the project without Docker, follow these steps:
### 1. Install dependencies
```bash
pip install -r requirements.txt
```
### 2. Configure PostgreSQL locally:
Ensure that PostgreSQL is running on your machine, and update the `DATABASES` section in `settings.py` to point to your local PostgreSQL database.

### 3.Run the application:
```bash
python manage.py runserver
```

## Deployment
This project is Dockerized, which makes deployment straightforward on most platforms. For cloud deployment or CI/CD automation, adjust the deployment settings in the Docker and `settings.py` configuration files to meet your specific needs.

## Additional Setup for Cloud Deployment
To deploy the application on AWS or any other cloud platform, follow these steps:
- Set up an RDS PostgreSQL instance on AWS and modify the environment variables to point to the remote database.
- Ensure proper security groups and inbound rules are set for your EC2 instance to allow traffic on port `8000`.
- Set up GitHub Actions or another CI/CD pipeline for automated deployment if required.
