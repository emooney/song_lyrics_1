from flask import Flask, render_template, jsonify, request
import os
from dotenv import load_dotenv
import lyricsgenius
import re
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Genius client
access_token = os.getenv('GENIUS_TOKEN')
genius = lyricsgenius.Genius(
    access_token,
    retries=3,
    verbose=True,  # Enable verbose logging
    remove_section_headers=True,
    timeout=15
)

# Update session headers
genius._session.headers.update({
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# Print current configuration
print(f"Genius API Configuration:")
print(f"Access Token: {access_token[:5]}...")
print(f"Headers: {genius._session.headers}")

def sanitize_filename(filename):
    """Convert song title to valid filename"""
    return re.sub(r'[^\w\s-]', '', filename).replace(' ', '_')

def get_songs():
    """Get list of all songs in songs directory"""
    if not os.path.exists('songs'):
        os.makedirs('songs')
    songs = []
    for file in os.listdir('songs'):
        if file.endswith('.txt'):
            title = file[:-4].replace('_', ' ')
            # Try to get artist from file content
            filepath = os.path.join('songs', file)
            artist = None
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if 'by' in first_line.lower():
                        artist = first_line.split('by')[-1].strip()
            except:
                pass
            songs.append({
                'title': title,
                'artist': artist,
                'filename': file
            })
    return sorted(songs, key=lambda x: x['title'].lower())

def save_lyrics(title, artist, lyrics):
    """Save lyrics to file"""
    if not os.path.exists('songs'):
        os.makedirs('songs')
    filename = f"{sanitize_filename(title)}.txt"
    filepath = os.path.join('songs', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        if artist:
            f.write(f"Lyrics by {artist}\n\n")
        f.write(lyrics)
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list_songs')
def list_songs():
    return jsonify({'songs': get_songs()})

@app.route('/get-lyrics/<filename>')
def get_lyrics_by_filename(filename):
    try:
        filepath = os.path.join('songs', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Song not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Try to extract artist from first line
            lines = content.split('\n')
            artist = None
            lyrics = content
            if lines[0].lower().startswith('lyrics by'):
                artist = lines[0].split('by')[-1].strip()
                lyrics = '\n'.join(lines[2:])  # Skip header and blank line
            
            return jsonify({
                'title': filename[:-4].replace('_', ' '),
                'artist': artist,
                'lyrics': lyrics
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process_song', methods=['POST'])
def process_song():
    try:
        data = request.get_json()
        input_text = data.get('input', '').strip()
        
        # Split input into title and artist if separator exists
        title = input_text
        artist = None
        if '|' in input_text:
            parts = [p.strip() for p in input_text.split('|', 1)]
            title = parts[0]
            artist = parts[1] if len(parts) > 1 else None
        
        print(f"Searching for - Title: {title}, Artist: {artist}")  # Debug log
        
        # Check if song already exists
        filename = f"{sanitize_filename(title)}.txt"
        filepath = os.path.join('songs', filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return jsonify({
                    'status': 'success',
                    'message': 'Song found in local storage',
                    'filename': filename,
                    'title': title,
                    'artist': artist,
                    'lyrics': content
                })
        
        # Search using Genius API
        try:
            print(f"Calling Genius API with title='{title}', artist='{artist}'")  # Debug log
            
            # Try multiple search approaches
            song = None
            search_attempts = [
                # Try exact search with artist
                lambda: genius.search_song(title, artist) if artist else None,
                # Try exact search without artist
                lambda: genius.search_song(title),
                # Try with 'by' between title and artist
                lambda: genius.search_song(f"{title} by {artist}") if artist else None,
                # Try with different artist formats
                lambda: genius.search_song(title, artist.replace('The ', '')) if artist and artist.startswith('The ') else None,
                lambda: genius.search_song(title, f"The {artist}") if artist and not artist.startswith('The ') else None,
                # Try searching just by artist first
                lambda: next((s for s in genius.search_artist(artist, max_songs=5).songs if s.title.lower() == title.lower()), None) if artist else None
            ]
            
            for attempt in search_attempts:
                try:
                    print(f"Trying new search attempt...")  # Debug log
                    result = attempt()
                    if result:
                        print(f"Found result: {result.title} by {result.artist}")  # Debug log
                        song = result
                        break
                except Exception as search_error:
                    print(f"Search attempt failed: {str(search_error)}")
                    continue
            
            if song:
                print(f"Song found: {song.title} by {song.artist}")  # Debug log
                # Save lyrics
                saved_filename = save_lyrics(title, artist or song.artist, song.lyrics)
                return jsonify({
                    'status': 'success',
                    'message': 'Lyrics downloaded successfully',
                    'filename': saved_filename,
                    'title': title,
                    'artist': artist or song.artist,
                    'lyrics': song.lyrics
                })
            else:
                print("No song found in Genius API")  # Debug log
                return jsonify({
                    'status': 'error',
                    'message': 'Song not found on Genius'
                }), 404
                
        except Exception as e:
            error_msg = str(e)
            print(f"Genius API Error: {error_msg}")  # Debug log
            
            if '403' in error_msg:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication failed. Please check your Genius API token.'
                }), 403
            elif '429' in error_msg:
                return jsonify({
                    'status': 'error',
                    'message': 'Rate limit exceeded. Please try again later.'
                }), 429
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Error accessing Genius API: {error_msg}'
                }), 500
            
    except Exception as e:
        print(f"General Error: {str(e)}")  # Debug log
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/delete-song/<filename>', methods=['DELETE'])
def delete_song(filename):
    try:
        filepath = os.path.join('songs', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Song not found'}), 404
        
        os.remove(filepath)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)