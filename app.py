from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import lyricsgenius
import json
import re
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Genius API
genius = lyricsgenius.Genius(os.getenv('GENIUS_TOKEN'))

# Ensure songs directory exists
SONGS_DIR = 'songs'
os.makedirs(SONGS_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clean_filename(filename):
    """Clean filename to be filesystem safe"""
    # Remove any characters that aren't alphanumeric, space, hyphen, or underscore
    cleaned = re.sub(r'[^\w\s-]', '', filename)
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Trim spaces from beginning and end
    cleaned = cleaned.strip()
    return cleaned

def load_songs():
    """Load all songs from the songs directory"""
    songs = []
    for filename in os.listdir(SONGS_DIR):
        if filename.endswith('.txt'):
            # Parse filename to get title and artist
            name_parts = filename[:-4].split(' - ', 1)  # Remove .txt and split on first ' - '
            title = name_parts[0]
            artist = name_parts[1] if len(name_parts) > 1 else None
            
            # Read lyrics from file
            with open(os.path.join(SONGS_DIR, filename), 'r', encoding='utf-8') as f:
                lyrics = f.read()
            
            songs.append({
                'title': title,
                'artist': artist,
                'lyrics': lyrics
            })
    return songs

def save_song(title, artist, lyrics):
    """Save song lyrics to a file"""
    if artist:
        filename = f"{clean_filename(title)} - {clean_filename(artist)}.txt"
    else:
        filename = f"{clean_filename(title)}.txt"
    
    filepath = os.path.join(SONGS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(lyrics)
    return filename

def fetch_lyrics(title, artist=None):
    """Fetch lyrics from Genius API"""
    search_term = f"{title} {artist}" if artist else title
    try:
        if not os.getenv('GENIUS_TOKEN'):
            logger.error("Error: GENIUS_TOKEN not found in environment variables")
            return None
            
        song = genius.search_song(title, artist)
        if song:
            return song.lyrics
        else:
            logger.info(f"No song found for search term: {search_term}")
    except Exception as e:
        logger.error(f"Error fetching lyrics from Genius API: {str(e)}")
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html', songs=load_songs())

@app.route('/search', methods=['POST'])
def search():
    logger.info("Received search request")
    data = request.get_json()
    input_text = data.get('text', '').strip()
    is_search = data.get('isSearch', False)
    
    logger.info(f"Search request - Text: {input_text}, IsSearch: {is_search}")
    
    # Parse input (format: "title | artist" or just "title")
    parts = [p.strip() for p in input_text.split('|', 1)]
    title = parts[0]
    artist = parts[1] if len(parts) > 1 else None
    
    logger.info(f"Parsed - Title: {title}, Artist: {artist}")
    
    # First check if we already have the lyrics
    songs = load_songs()
    logger.info(f"Loaded {len(songs)} songs")
    
    for song in songs:
        logger.info(f"Comparing with song - Title: {song['title']}, Artist: {song['artist']}")
        if song['title'].lower() == title.lower() and (not artist or (song['artist'] and song['artist'].lower() == artist.lower())):
            logger.info("Found match! Returning lyrics")
            return jsonify({'lyrics': song['lyrics']})
    
    logger.info("No local match found")
    
    # If not found locally, fetch from Genius only if this is a search request
    if is_search:
        logger.info("Attempting to fetch from Genius")
        lyrics = fetch_lyrics(title, artist)
        if lyrics:
            logger.info("Found lyrics from Genius, saving")
            save_song(title, artist, lyrics)
            return jsonify({'lyrics': lyrics})
    
    logger.info("No lyrics found")
    return jsonify({'error': 'Lyrics not found'}), 404

@app.route('/delete', methods=['POST'])
def delete_song():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        title = data.get('title')
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        artist = data.get('artist', '').strip()
        
        # Create filename same way as save_song
        if artist:
            filename = f"{clean_filename(title)} - {clean_filename(artist)}.txt"
        else:
            filename = f"{clean_filename(title)}.txt"
            
        filepath = os.path.join(SONGS_DIR, filename)
        
        print(f"Attempting to delete: {filepath}")  # Debug log
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'Song file not found: {filename}'}), 404

        try:
            os.remove(filepath)
            return jsonify({'success': True})
        except PermissionError:
            return jsonify({'error': 'Permission denied while deleting file'}), 403
        except OSError as e:
            return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/get_lyrics', methods=['POST'])
def get_lyrics():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        title = data.get('title')
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        artist = data.get('artist', '').strip()
        
        # Create filename same way as save_song
        if artist:
            filename = f"{clean_filename(title)} - {clean_filename(artist)}.txt"
        else:
            filename = f"{clean_filename(title)}.txt"
            
        filepath = os.path.join(SONGS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'Lyrics file not found: {filename}'}), 404

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lyrics = f.read()
            return jsonify({'success': True, 'lyrics': lyrics})
        except Exception as e:
            return jsonify({'error': f'Error reading lyrics: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
