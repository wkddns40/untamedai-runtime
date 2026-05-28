from tests.golden._diff import diff_events, merge_stream_chunks, normalize_events


def test_merge_collapses_adjacent_stream_chunks() -> None:
    events = [
        {"type": "stream", "content": "Hello"},
        {"type": "stream", "content": ", "},
        {"type": "stream", "content": "world"},
        {"type": "end", "content": "Hello, world", "intent": "chat"},
    ]

    assert merge_stream_chunks(events) == [
        {"type": "stream", "content": "Hello, world"},
        {"type": "end", "content": "Hello, world", "intent": "chat"},
    ]


def test_normalize_collapses_interior_whitespace() -> None:
    events = [
        {"type": "stream", "content": "Hello    \n world"},
        {"type": "end", "content": "Hello\tworld", "intent": "chat"},
    ]

    assert normalize_events(events) == [
        {"type": "stream", "content": "Hello world"},
        {"type": "end", "content": "Hello world", "intent": "chat"},
    ]


def test_diff_empty_for_equivalent_chunking() -> None:
    expected = [
        {"type": "stream", "content": "Hello, world"},
        {"type": "end", "content": "Hello, world", "intent": "chat"},
    ]
    actual = [
        {"type": "stream", "content": "Hello"},
        {"type": "stream", "content": ","},
        {"type": "stream", "content": " world"},
        {"type": "end", "content": "Hello,  world", "intent": "chat"},
    ]

    assert diff_events(actual, expected) == []


def test_diff_flags_content_mismatch() -> None:
    actual = [{"type": "stream", "content": "hi"}]
    expected = [{"type": "stream", "content": "bye"}]
    diff = diff_events(actual, expected)

    assert diff
    assert "hi" in "\n".join(diff)
    assert "bye" in "\n".join(diff)
