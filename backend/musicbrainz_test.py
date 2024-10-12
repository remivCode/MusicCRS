import musicbrainzngs
import time
import json

# Set up user agent information
musicbrainzngs.set_useragent("MyMusicApp", "1.0", "r.vialleton@stud.uis.n")

def fetch_recordings(limit=100, batch_size=100, sleep_time=1.0):    
    recordings = []
    offset = 0
    
    while len(recordings) < limit:
        try:
            # Search for recordings with pagination
            result = musicbrainzngs.search_recordings(query="*", limit=batch_size, offset=offset)
            recordings_batch = result['recording-list']
            
            if not recordings_batch:
                print("No more recordings found, stopping.")
                break

            recordings.extend(recordings_batch)
            print(f"Fetched {len(recordings)} recordings so far.")
            
            # Increment offset for pagination
            offset += batch_size
            
            # Sleep to respect rate limits
            time.sleep(sleep_time)
            
        except musicbrainzngs.WebServiceError as e:
            print(f"Error fetching data: {e}")
            time.sleep(5)  # Wait and retry in case of an error

    return recordings

songs_data = fetch_recordings(limit=100, batch_size=100)

def save_to_file(data, filename="songs_data.json"):
    with open(filename, 'w') as f:
        json.dump(data, f)

# Save the fetched songs data to a JSON file
save_to_file(songs_data)