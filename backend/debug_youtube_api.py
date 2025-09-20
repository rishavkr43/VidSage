# Quick debug to understand the YouTube API
from youtube_transcript_api import YouTubeTranscriptApi
import inspect

# Check the fetch method signature
print("Fetch method signature:")
print(inspect.signature(YouTubeTranscriptApi.fetch))

# Try different approaches
try:
    # Try as class method
    result = YouTubeTranscriptApi().fetch("dQw4w9WgXcQ")
    print(f"Instance method works: {len(result)} segments")
except Exception as e:
    print(f"Instance method failed: {e}")

try:
    # Try as static method with different signature
    result = YouTubeTranscriptApi.fetch("dQw4w9WgXcQ")
    print(f"Static method works: {len(result)} segments")
except Exception as e:
    print(f"Static method failed: {e}")

# Check if there are other methods
methods = [m for m in dir(YouTubeTranscriptApi) if not m.startswith('_')]
print(f"All available methods: {methods}")

# Check the list method too
try:
    transcripts = YouTubeTranscriptApi.list("dQw4w9WgXcQ")
    print(f"List method works: {transcripts}")
except Exception as e:
    print(f"List method failed: {e}")