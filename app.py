from flask import Flask, render_template, request, jsonify
import lyricsgenius
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get Genius API token from environment variable
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')
if not GENIUS_TOKEN:
    raise ValueError("GENIUS_TOKEN not found in environment variables. Please check your .env file.")

genius = lyricsgenius.Genius(GENIUS_TOKEN)

# Create songs directory if it doesn't exist
SONGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'songs')
os.makedirs(SONGS_DIR, exist_ok=True)

def save_lyrics(song_name, lyrics, artist=None):
    # Create metadata string
    metadata = f"Title: {song_name}\n"
    if artist:
        metadata += f"Artist: {artist}\n"
    metadata += f"\n{lyrics}"
    
    # Create a valid filename from the song name and artist
    base_name = song_name
    if artist:
        base_name += f" - {artist}"
    filename = "".join(x for x in base_name if x.isalnum() or x in (' ', '-', '_')) + '.txt'
    
    # Create full path for the file
    filepath = os.path.join(SONGS_DIR, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        return filename, False
    
    # Save the lyrics with metadata to a file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(metadata)
    return filename, True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_lyrics():
    data = request.get_json()
    songs_input = data.get('songs', '').strip().split('\n')
    results = []
    
    for song_line in songs_input:
        if '|' in song_line:
            song_name, artist = song_line.split('|', 1)
        else:
            song_name, artist = song_line, None
            
        song_name = song_name.strip()
        artist = artist.strip() if artist else None
        
        try:
            if artist:
                song = genius.search_song(song_name, artist)
            else:
                song = genius.search_song(song_name)
                
            if song:
                filename, is_new = save_lyrics(song.title, song.lyrics, song.artist)
                results.append({
                    'song': song.title,
                    'artist': song.artist,
                    'status': 'success' if is_new else 'already_exists',
                    'filename': filename
                })
            else:
                results.append({
                    'song': song_name,
                    'artist': artist,
                    'status': 'not_found'
                })
        except Exception as e:
            results.append({
                'song': song_name,
                'artist': artist,
                'status': 'error',
                'message': str(e)
            })
    
    return jsonify(results)

@app.route('/view_lyrics', methods=['POST'])
def view_lyrics():
    data = request.get_json()
    search_term = data.get('song', '').strip()
    
    # List all files in songs directory
    songs = os.listdir(SONGS_DIR)
    matching_songs = [song for song in songs if search_term.lower() in song.lower()]
    
    if not matching_songs:
        return jsonify({
            'status': 'not_found',
            'message': f'No songs found matching "{search_term}"'
        })
    
    results = []
    for song_file in matching_songs:
        filepath = os.path.join(SONGS_DIR, song_file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()
                
                title = first_line.replace('Title: ', '') if first_line.startswith('Title: ') else ''
                artist = second_line.replace('Artist: ', '') if second_line.startswith('Artist: ') else None
                
                lyrics = f.read()
            results.append({
                'filename': song_file,
                'title': title,
                'artist': artist,
                'lyrics': lyrics,
                'status': 'success'
            })
        except Exception as e:
            results.append({
                'filename': song_file,
                'status': 'error',
                'message': str(e)
            })
    
    return jsonify(results)

@app.route('/list-songs')
def list_songs():
    songs = []
    for filename in os.listdir(SONGS_DIR):
        if filename.endswith('.txt'):
            # Extract title and artist from filename
            name = os.path.splitext(filename)[0]
            parts = name.replace('_', ' ').split(' - ', 1)
            
            title = parts[0].strip()
            artist = parts[1].strip() if len(parts) > 1 else None
            
            songs.append({
                'filename': filename,
                'title': title,
                'artist': artist
            })
    return jsonify(sorted(songs, key=lambda x: x['title'].lower()))

@app.route('/get-lyrics/<filename>')
def get_lyrics_by_file(filename):
    try:
        filepath = os.path.join(SONGS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Song not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lyrics = f.read()
        
        # Extract title and artist from filename
        name = os.path.splitext(filename)[0]
        parts = name.replace('_', ' ').split(' - ', 1)
        
        title = parts[0].strip()
        artist = parts[1].strip() if len(parts) > 1 else None
        
        return jsonify({
            'title': title,
            'artist': artist,
            'lyrics': lyrics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
