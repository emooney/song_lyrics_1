from flask import Flask, render_template, request, jsonify
import lyricsgenius
import os
import re
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

def clean_lyrics(lyrics):
    # Split lyrics into lines
    lines = lyrics.split('\n')
    
    # Process the lines with proper spacing
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        current_line = line.strip()
        
        # Skip empty lines at the start of the file
        if not current_line and not cleaned_lines:
            continue
            
        # Handle Title and Artist lines
        if current_line.startswith('Title:') or current_line.startswith('Artist:'):
            cleaned_lines.append(current_line)
            if not (i + 1 < len(lines) and lines[i + 1].strip() == ''):
                cleaned_lines.append('')
            continue
            
        # Skip unwanted lines
        if (current_line.lower().endswith('lyrics') or 
            'you might also like' in current_line.lower() or
            re.match(r'.*\d+\s*[Ee]mbed\s*$', current_line)):
            continue
            
        # Handle section markers
        if current_line.startswith('['):
            # Skip duplicate section markers
            if (cleaned_lines and 
                (cleaned_lines[-1].startswith('[') or 
                 (len(cleaned_lines) > 1 and cleaned_lines[-2].startswith('[')))):
                continue
                
            # Add empty line before section marker if needed
            if cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append('')
            cleaned_lines.append(current_line)
            
            # Add empty line after section marker if next line isn't empty
            if i + 1 < len(lines) and lines[i + 1].strip():
                cleaned_lines.append('')
            continue
            
        # Handle regular content lines
        if current_line:
            cleaned_lines.append(current_line)
        # Handle empty lines
        elif cleaned_lines and cleaned_lines[-1].strip():
            cleaned_lines.append('')
    
    # Clean up multiple consecutive empty lines
    final_lines = []
    prev_empty = False
    for line in cleaned_lines:
        if line.strip() or not prev_empty:
            final_lines.append(line)
            prev_empty = not line.strip()
    
    # Ensure the file ends with a newline
    if final_lines and final_lines[-1].strip():
        final_lines.append('')
    
    return '\n'.join(final_lines)

def save_lyrics(song_name, lyrics, artist=None):
    # Clean the lyrics first
    cleaned_lyrics = clean_lyrics(lyrics)
    
    # Create metadata string
    metadata = f"Title: {song_name}\n"
    if artist:
        metadata += f"Artist: {artist}\n"
    metadata += f"\n{cleaned_lyrics}"
    
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

# This method is triggered when the user first opens the page in the browser.
@app.route('/list-songs', methods=['GET'])
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

@app.route('/delete-song/<filename>', methods=['DELETE'])
def delete_song(filename):
    try:
        file_path = os.path.join(SONGS_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Song file not found'}), 404
        
        os.remove(file_path)
        return jsonify({'message': 'Song deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
