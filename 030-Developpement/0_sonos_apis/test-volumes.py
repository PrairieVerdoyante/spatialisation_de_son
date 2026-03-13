#!/usr/bin/env python
import time
import math
from soco import SoCo
from soco.music_library import MusicLibrary
if __name__ == '__main__':
    sonos = SoCo('192.168.123.66') # Pass in the IP of your Sonos speaker
    library = MusicLibrary(sonos)
    uri = "x-file-cifs://PC-SARAH/SonosMusic/piano_sound.wav"
    search_term = "piano_sound" # Your song title
    tracks = library.get_music_library_information(
    'tracks', search_term=search_term, start=0, max_items=10
    )
if tracks:
    track = tracks[0]
    print(f"Playing: {track.title} ")
    # Clear queue and add the track
    sonos.clear_queue()
    sonos.add_to_queue(track)
    # Start playing from the queue
    sonos.play_uri(uri)
    # Start dynamic volume control
    start_time = time.time()
    period = 5 # full sine wave cycle in seconds
    base_volume = 0 # min volume
    max_volume = 30 # max volume
    gain1 = 0
    gain2 = 1
    start_time = time.time()
    period = 5
    while True:
        current_time = time.time() - start_time
        gain1 = (math.sin(2 * math.pi * current_time / period) + 1) / 2
        gain2 = 1 - gain1
        volume = int(base_volume + gain1 * (max_volume - base_volume))
        sonos.volume = volume
else:
    print(f"No track found with title: {search_term}")