# Song Lyrics Finder

A web application that helps you find, save, and manage song lyrics using the Genius API.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Genius API token:
   - Go to https://genius.com/api-clients
   - Create an account if you don't have one
   - Create a new API client
   - Copy your access token

3. Create a `.env` file in the root directory and add your Genius token:
```
GENIUS_TOKEN=your_token_here
```

## Running the Application

1. Run the Flask application:
```bash
python app.py
```

2. Open your web browser and go to `http://localhost:5000`

Example input:
```
Bohemian Rhapsody | Queen
Yesterday | The Beatles
Imagine
```

## Features
- All songs in the 'songs' directory are loaded automatically when the app starts.
- Lyrics are fetched from Genius API when the songs are not found locally and the user hits'Search'.
- Lyrics are saved in the 'songs' directory.
- Dynamically filters songs being displayed based on the input text.
- View lyrics when a song is selected.
- Each song has a delete button to remove it from the list.
- Lyrics are formatted with newlines and indentation.
- Clean and responsive web interface
- Secure configuration using environment variables
- Error handling and status feedback
- dark and light themes
