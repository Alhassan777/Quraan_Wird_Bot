# Quraan Werd Tracker Bot

A production-ready Telegram bot for tracking daily Quraan reading (Werd) with streak calculations and personalized reminders.

## Features

- Track daily Quraan reading completions with various checkmark emojis (✅, ✔️, ✓, ☑️, and others)
- Cross-platform emoji support for compatibility across all devices
- Calculate and maintain user reading streaks
- Support for reverse streaks to track continuous reading
- Multi-language support (English and Arabic)
- Personalized reminders with inspirational Quraan quotes
- Missed streak reminders
- Timezone support (defaulting to America/Los_Angeles)
- Supabase PostgreSQL database integration
- Monitoring with metrics tracking

## Supported Check Mark Symbols

The bot recognizes multiple forms of check mark symbols across different platforms:

- ✅ White Heavy Check Mark
- ✔️ Heavy Check Mark (with variation selector)
- ✔ Heavy Check Mark (without variation selector)
- ✓ Check Mark
- ☑️ Ballot Box with Check (with variation selector)
- ☑ Ballot Box with Check (without variation selector)
- 🗸 Light Check Mark

This ensures users can mark their daily Quraan reading regardless of their device.

## Architecture

This application uses a modern, scalable architecture:

- **Supabase**: Provides PostgreSQL database and authentication
- **Python Telegram Bot**: For Telegram API integration
- **Docker**: For containerization and easy deployment

## Database Structure

The bot uses the following database tables:

- **users**: Stores user information, language preferences, and timezones
- **streaks**: Tracks current streak, reverse streak, and last check-in
- **check_ins**: Records individual reading check-ins
- **message_templates**: Stores motivational messages and reminders
- **reminders**: Manages user reminder settings

## Requirements

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Supabase account and project

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd quraan-werd-tracker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   LOG_LEVEL=INFO
   ```

5. Initialize the database:
   ```bash
   python -m bot.database.create_tables
   ```

6. Run the bot:
   ```bash
   python -m bot.main
   ```

### Railway Deployment

1. Create a Railway account at [railway.app](https://railway.app)

2. Install the Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```
   
3. Login to Railway:
   ```bash
   railway login
   ```

4. Link your project:
   ```bash
   railway link
   ```

5. Set environment variables:
   ```bash
   railway variables set TELEGRAM_TOKEN=your_telegram_bot_token
   railway variables set SUPABASE_URL=your_supabase_url
   railway variables set SUPABASE_KEY=your_supabase_key
   railway variables set LOG_LEVEL=INFO
   ```

6. Deploy your app:
   ```bash
   railway up
   ```

## Bot Commands

- `/start` - Start the bot and select language
- `/help` - Get help information
- `/streak` - View your current streak
- `/settimezone` - Set your timezone (defaults to America/Los_Angeles)
- `/setreminder` - Configure daily reminders

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE) 