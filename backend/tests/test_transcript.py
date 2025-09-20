# backend/tests/test_transcript.py
import app.services.transcript as transcript_module


def test_fetch_transcript_text_monkeypatched(monkeypatch):
    # Sample transcript shape returned by youtube_transcript_api
    sample_segments = [
        {"text": "Hello world", "start": 0, "duration": 1},
        {"text": "This is a sample transcript.", "start": 1, "duration": 2},
    ]

    # Monkeypatch the get_transcript function used inside our service
    monkeypatch.setattr(
        transcript_module,
        "YouTubeTranscriptApi",
        type("DummyAPI", (), {"get_transcript": staticmethod(lambda video_id, languages=None: sample_segments)}),
    )

    combined = transcript_module.fetch_transcript_text("dummy_video_id", languages=["en"])
    assert "Hello world" in combined
    assert "sample transcript" in combined
