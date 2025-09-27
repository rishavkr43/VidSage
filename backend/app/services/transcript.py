# backend/app/services/transcript.py (patch)
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def fetch_transcript_text(video_id: str, languages: list[str] = None) -> str:
    """
    Fetch transcript for a Youtube video and return concatenated text.
    Tries preferred languages first, otherwise tries available transcripts.
    Raises an exception if transcripts not available.
    """
    if languages is None:
        languages = ["en"]

    try:
        api = YouTubeTranscriptApi()

        try:
            fetched_transcript = api.fetch(video_id, languages=languages)
        except (NoTranscriptFound, TranscriptsDisabled):
            fetched_transcript = api.fetch(video_id)

        # Prefer the library helper that returns raw dicts if available
        transcript_list = None
        if hasattr(fetched_transcript, "to_raw_data"):
            try:
                transcript_list = fetched_transcript.to_raw_data()
            except Exception:
                transcript_list = None

        # Otherwise try common fallbacks: .fetch(), iterate, or assume it's already a list
        if transcript_list is None:
            if hasattr(fetched_transcript, "fetch"):
                try:
                    transcript_list = fetched_transcript.fetch()
                except Exception:
                    transcript_list = None

        if transcript_list is None:
            # If it's iterable (e.g. yields snippet objects), cast to list
            if hasattr(fetched_transcript, "__iter__"):
                transcript_list = list(fetched_transcript)
            else:
                # As a last resort assume fetched_transcript is already the data
                transcript_list = fetched_transcript

        # Extract text safely whether segments are dicts or objects
        def _segment_text(seg):
            if isinstance(seg, dict):
                return seg.get("text", "") or ""
            # Some libs use dataclass/objects with .text or .get_text or __dict__
            if hasattr(seg, "text"):
                return getattr(seg, "text") or ""
            # fallback to attribute names seen in debug output
            if hasattr(seg, "to_dict"):
                try:
                    d = seg.to_dict()
                    return d.get("text", "") or ""
                except Exception:
                    pass
            # final fallback: try mapping-like access
            try:
                return seg["text"]  # may raise
            except Exception:
                return ""

        texts = [_segment_text(s) for s in transcript_list]
        # Filter out empty pieces and join
        text = " ".join(t for t in texts if t)
        return text

    except TranscriptsDisabled as te:
        logger.error("Transcripts disabled for video %s: %s", video_id, te)
        raise Exception(f"Transcripts are disabled for this video: {te}")

    except NoTranscriptFound as ntf:
        logger.error("No transcript found for video %s: %s", video_id, ntf)
        raise Exception(f"No transcript available for this video: {ntf}")

    except Exception as e:
        logger.exception("Unexpected error fetching transcript for %s: %s", video_id, e)
        raise Exception(f"Error fetching transcript: {e}")