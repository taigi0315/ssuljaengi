"""Core utility functions."""

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds to ASS timestamp (H:MM:SS.cs).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)

    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
