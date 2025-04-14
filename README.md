# Quraan Werd Tracker Bot

A production-ready Telegram bot for tracking daily Quraan reading (Werd) with streak calculations and reminders.

You will find it at t.me/WirdiBOt.

## Features

- Track daily Quraan reading completions with checkmark emoji (✅ or ✔️)
- Calculate and maintain user streaks
- Group dashboard to view all participants' streaks
- Anti-spam: ignores duplicate checkmarks in the same 24-hour window
- Admin-only group settings
- Daily reminders with inspirational Quraan quotes
- Missed streak reminders sent privately
- Timezone support (defaulting to PT/America/Los_Angeles)
- PostgreSQL database for scalable data storage
- Redis caching for improved performance
- Prometheus metrics for monitoring
- Containerized with Docker for easy deployment
- Horizontal scaling capability

## Production Architecture

This application uses a modern, scalable architecture:

- **PostgreSQL**: For persistent data storage
- **Redis**: For caching frequently accessed data
- **Prometheus & Grafana**: For monitoring and metrics
- **Docker & Docker Compose**: For containerization and orchestration

## Requirements

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Quick Start with Docker Compose

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd quraan-werd-tracker
   ```

2. Create a `.env` file with your configuration:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql://postgres:postgres@postgres:5432/werd_tracker
   REDIS_URL=redis://redis:6379/0
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

This will start the bot along with PostgreSQL, Redis, Prometheus, and Grafana.

## Manual Setup

If you prefer to run components separately:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up PostgreSQL:
   ```bash
   # Create database
   createdb werd_tracker
   ```

3. Set up Redis:
   ```bash
   # Start Redis server
   redis-server
   ```

4. Configure environment variables:
   ```bash
   export TELEGRAM_TOKEN=your_telegram_bot_token
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/werd_tracker
   export REDIS_URL=redis://localhost:6379/0
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## Bot Commands

- `/start` - Start the bot
- `/help` - Get help information
- `/streak` - View your current streak
- `/dashboard` - View the group dashboard (in groups)
- `/settimezone` - Set your timezone (defaults to PT)
- `/setreminder` - Set daily reminders

## Monitoring

- Prometheus metrics are available at http://localhost:9090
- Grafana dashboards are available at http://localhost:3000

## Scaling for Production

The application is designed to scale horizontally:

1. Deploy multiple instances behind a load balancer
2. Use a managed PostgreSQL service (AWS RDS, Google Cloud SQL)
3. Use a managed Redis service (AWS ElastiCache, Google Cloud Memorystore)
4. Set up proper monitoring and alerting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 