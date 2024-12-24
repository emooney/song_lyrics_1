document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const lyricsDisplay = document.getElementById('lyricsDisplay');
    const songsList = document.getElementById('songsList');
    const themeToggle = document.getElementById('themeToggle');
    const backButton = document.getElementById('backButton');
    const songsListView = document.getElementById('songsListView');
    const lyricsView = document.getElementById('lyricsView');
    const lyricsSongTitle = document.getElementById('lyricsSongTitle');
    const lyricsTitle = document.getElementById('lyricsTitle');
    const lyricsContent = document.getElementById('lyricsContent');

    // Theme handling
    let isDarkTheme = localStorage.getItem('darkTheme') === 'true';
    updateTheme();

    themeToggle.addEventListener('click', () => {
        isDarkTheme = !isDarkTheme;
        localStorage.setItem('darkTheme', isDarkTheme);
        updateTheme();
    });

    function updateTheme() {
        document.body.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
    }

    // View switching
    function showLyricsView() {
        console.log('Showing lyrics view');
        document.querySelector('.container').classList.add('lyrics-mode');
        songsListView.style.display = 'none';
        lyricsView.style.display = 'block';
        lyricsView.classList.remove('d-none');
    }

    function showSongsListView() {
        console.log('Showing songs list view');
        document.querySelector('.container').classList.remove('lyrics-mode');
        songsListView.style.display = 'block';
        lyricsView.style.display = 'none';
        lyricsView.classList.add('d-none');
    }

    backButton.addEventListener('click', function(e) {
        e.preventDefault();
        showSongsListView();
    });

    // Filter songs as user types
    searchInput.addEventListener('input', function() {
        const searchText = this.value.toLowerCase();
        const songItems = songsList.getElementsByClassName('song-item');
        
        Array.from(songItems).forEach(item => {
            const title = item.querySelector('.song-title').textContent.toLowerCase();
            const artist = item.querySelector('.song-artist')?.textContent.toLowerCase() || '';
            const shouldShow = title.includes(searchText) || artist.includes(searchText);
            item.style.display = shouldShow ? '' : 'none';
        });
    });

    // Search functionality
    searchButton.addEventListener('click', searchLyrics);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLyrics();
        }
    });

    function searchLyrics() {
        const searchText = searchInput.value.trim();
        if (!searchText) return;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                text: searchText,
                isSearch: true
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                lyricsDisplay.textContent = 'Lyrics not found';
            } else {
                lyricsDisplay.textContent = data.lyrics;
                const parts = searchText.split('|').map(part => part.trim());
                lyricsSongTitle.textContent = parts[1] ? `${parts[0]} - ${parts[1]}` : parts[0];
                showLyricsView();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            lyricsDisplay.textContent = 'Error fetching lyrics';
        });
    }

    // Song click functionality
    document.addEventListener('click', function(e) {
        const songItem = e.target.closest('.song-item');
        if (!songItem || e.target.classList.contains('delete-btn')) return;
        
        const title = songItem.querySelector('.song-title').textContent;
        const artistEl = songItem.querySelector('.song-artist');
        const artist = artistEl ? artistEl.textContent.replace(/^[\s-]+/, '').trim() : '';

        console.log('Fetching lyrics for:', { title, artist });

        fetch('/get_lyrics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                title: title,
                artist: artist 
            })
        })
        .then(response => {
            console.log('Lyrics response:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to fetch lyrics');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Lyrics fetched successfully');
            if (data.success) {
                // Show lyrics view
                document.getElementById('songsList').style.display = 'none';
                const lyricsView = document.getElementById('lyricsView');
                lyricsView.style.display = 'block';
                
                // Update lyrics content
                lyricsTitle.textContent = artist ? `${title} - ${artist}` : title;
                
                lyricsContent.textContent = data.lyrics;
                
                // Show back button
                document.getElementById('backButton').style.display = 'block';
            } else {
                throw new Error(data.error || 'Failed to fetch lyrics');
            }
        })
        .catch(error => {
            console.error('Lyrics error:', error);
            alert(error.message || 'Error fetching lyrics');
        });
    });

    // Back button functionality
    document.getElementById('backButton').addEventListener('click', function() {
        document.getElementById('lyricsView').style.display = 'none';
        document.getElementById('songsList').style.display = 'block';
        this.style.display = 'none';
    });

    // Delete functionality
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.delete-btn');
        if (!deleteBtn) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const title = deleteBtn.dataset.title.trim();
        const artist = deleteBtn.dataset.artist ? deleteBtn.dataset.artist.trim() : '';

        console.log('Attempting to delete song:', { title, artist });

        if (!title) {
            console.error('No title found for delete button');
            return;
        }

        if (!confirm(`Are you sure you want to delete "${title}${artist ? ` by ${artist}` : ''}"?`)) {
            return;
        }

        fetch('/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                title: title,
                artist: artist 
            })
        })
        .then(response => {
            console.log('Delete response:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to delete song');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Delete success:', data);
            if (data.success) {
                window.location.reload();
            } else {
                throw new Error(data.error || 'Failed to delete song');
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            alert(error.message || 'Error deleting song');
        });
    });
});
