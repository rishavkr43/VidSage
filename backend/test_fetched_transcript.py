# Test what the FetchedTranscript object returns
from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()
fetched = api.fetch("dQw4w9WgXcQ")

print(f"Type of fetched object: {type(fetched)}")
print(f"Dir of fetched object: {[m for m in dir(fetched) if not m.startswith('_')]}")

# Test if it's iterable
try:
    for i, segment in enumerate(fetched):
        print(f"Segment {i}: {segment}")
        if i >= 2:  # Just show first 3
            break
except Exception as e:
    print(f"Not directly iterable: {e}")

# Test if it has a transcript property
if hasattr(fetched, 'transcript'):
    print(f"Has transcript property: {type(fetched.transcript)}")
    if hasattr(fetched.transcript, '__iter__'):
        print(f"First transcript segment: {list(fetched.transcript)[0]}")

# Test other possible attributes
for attr in ['segments', 'data', 'text', 'transcript_data']:
    if hasattr(fetched, attr):
        print(f"Has {attr} attribute: {getattr(fetched, attr)}")