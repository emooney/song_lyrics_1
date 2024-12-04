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

## Usage

1. Enter songs in the text area, one per line
2. Format: `Song Name | Artist` (Artist is optional)
3. Click "Find Lyrics" to search and save the lyrics
4. View saved lyrics by clicking on song titles in the list
5. All lyrics are automatically saved in the `songs` directory

Example input:
```
Bohemian Rhapsody | Queen
Yesterday | The Beatles
Imagine
```

## Features

- Search for lyrics by song name and artist
- Support for multiple song searches at once
- View saved lyrics directly in the web interface
- List all previously saved songs
- Automatic saving of lyrics to text files
- Clean and responsive web interface
- Secure configuration using environment variables
- Error handling and status feedback
