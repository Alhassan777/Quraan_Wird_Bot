# Quran Tafsir Gemini Pipeline

This pipeline processes Quran verses from text or images using Google's Gemini AI models, identifies the verses, and provides their tafsir (exegesis) from various scholarly sources.

## Features

- Extract Quran verses from text or images (with OCR)
- Strip Arabic diacritical marks (تشكيل) to optimize search
- Identify the exact Surah and Ayah numbers
- Provide tafsir (interpretation) from multiple scholarly sources
- Integration with Telegram for handling photos sent through the bot
- Privacy-focused design with no persistent data storage
- Validation to ensure extracted text is an actual Quran verse

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token (if using Telegram)
   ```

## Getting a Gemini API Key

1. Go to the [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add it to your `.env` file

## Usage

### Text Input

Process a Quran verse from text:

```python
from gemini_pipeline import get_tafsir_from_text

# Example Quran verse text (Al-Fatiha, 1:1)
verse_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

# Get tafsir
tafsir_result = get_tafsir_from_text(verse_text)

# Access the tafsir content
print(tafsir_result["verse_info"])  # Information about the verse
print(tafsir_result["tafsir_content"])  # The tafsir content
```

### Image Input

Process a Quran verse from an image:

```python
from gemini_pipeline import get_tafsir_from_image
from PIL import Image

# Load an image containing a Quran verse
image = Image.open("quran_verse_image.jpg")

# Get tafsir
tafsir_result = get_tafsir_from_image(image)

# Access the tafsir content
print(tafsir_result["verse_info"])  # Information about the verse
print(tafsir_result["tafsir_content"])  # The tafsir content
```

### Telegram Integration

To use the pipeline with Telegram:

1. Run the Telegram example bot:
   ```
   python gemini_pipeline/telegram_example.py
   ```
2. Open Telegram and search for your bot using the bot username
3. Send a text message containing a Quran verse or a photo of a Quran verse

## Validation Feature

The pipeline includes a validation mechanism to ensure that extracted text is an actual Quran verse. This prevents processing non-Quranic text or unclear images.

### Using Validation with Text

```python
from gemini_pipeline import get_tafsir_from_text, InvalidQuranVerseError

try:
    # Validate that this is a Quran verse
    result = get_tafsir_from_text("Your text here", validate=True)
    print("Valid Quran verse!")
except InvalidQuranVerseError as e:
    print(f"Not a Quran verse: {e.message}")
    print(f"Confidence: {e.confidence}%")
```

### Using Validation with Images

```python
from gemini_pipeline import get_tafsir_from_image, InvalidQuranVerseError

try:
    # Set minimum confidence threshold (0-100)
    result = get_tafsir_from_image("image.jpg", min_confidence=50)
    print("Valid Quran verse in image!")
except InvalidQuranVerseError as e:
    print(f"Not a Quran verse: {e.message}")
    print(f"Extracted text: {e.text}")
```

### Customizing Confidence Threshold

You can adjust the minimum confidence threshold for image validation:

```python
# Higher threshold (more strict)
result = get_tafsir_from_image("image.jpg", min_confidence=75)

# Lower threshold (more permissive)
result = get_tafsir_from_image("image.jpg", min_confidence=30)
```

## Customizing Tafsir Sources

You can specify which tafsir sources to use:

```python
from gemini_pipeline import get_tafsir_from_text

# Example Quran verse
verse_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

# Specify tafsir sources
tafsir_sources = ["Ibn Kathir", "Al-Tabari"]

# Get tafsir using specific sources
tafsir_result = get_tafsir_from_text(verse_text, tafsir_sources)
```

## Data Privacy & Security

This pipeline is designed with privacy in mind:

- Images and text are processed immediately and not stored permanently
- Temporary files are automatically deleted after processing
- Memory is cleared using garbage collection
- No data is persisted in databases
- API calls only store the minimal data required for processing
- Automatic cleanup runs periodically and on program exit

You can manually trigger cleanup with:

```python
from gemini_pipeline import cleanup_resources

# Call this after processing or when needed
cleanup_resources()
```

## Scaling for Production

For deploying in a production environment with high traffic:

### Containerization

The pipeline can be deployed in Docker containers for easy scaling:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "gemini_pipeline/telegram_example.py"]
```

### Load Balancing

- Deploy multiple instances behind a load balancer
- Use a message queue system like RabbitMQ or Redis for handling high volumes of requests
- Implement rate limiting to prevent API quota exhaustion

### Monitoring

Add monitoring to track:
- API usage and quotas
- Processing times
- Error rates
- Temporary storage usage

### Security Considerations

- Use secrets management for API keys
- Implement request validation
- Set up proper logging (without sensitive data)
- Regular security audits

## Examples

Check the example scripts:

- `gemini_pipeline/example.py` - Basic examples for text and image input
- `gemini_pipeline/telegram_example.py` - Example for Telegram bot integration
- `gemini_pipeline/validation_example.py` - Examples of using the validation feature

## License

This project is licensed under the MIT License. 