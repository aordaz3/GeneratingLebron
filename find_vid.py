from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi


DEFAULT_QUERIES = [
    "LeBron James postgame interview full",
    "LeBron James press conference full interview",
    "LeBron James media availability full",
    "LeBron James locker room interview full",
]

INTERVIEW_TERMS = (
    "interview",
    "postgame",
    "post game",
    "press conference",
    "media availability",
    "locker room",
    "full",
)

SKIP_TITLE_TERMS = (
    "reaction",
    "reacts",
    "debate",
    "first take",
    "undisputed",
    "highlights",
    "mixtape",
    "compilation",
    "impersonation",
    "parody",
    "funny",
    "comedy",
    "skit",
    "satire",
    "supremedreams",
    "original creator",
    "locker room videos",
    "nba 2k",
)

SKIP_TEXT_PATTERNS = (
    r"\blike and subscribe\b",
    r"\bsubscribe\b",
    r"\bthanks for watching\b",
    r"\bwelcome back\b",
    r"\bmake sure you\b",
    r"\bthis video\b",
    r"\bthe channel\b",
)

QUESTION_STARTERS = (
    "lebron",
    "bron",
    "what",
    "how",
    "why",
    "when",
    "where",
    "who",
    "can",
    "could",
    "do",
    "did",
    "does",
    "is",
    "are",
    "was",
    "were",
    "would",
    "will",
    "have",
    "has",
)


@dataclass(frozen=True)
class Video:
    video_id: str
    title: str
    url: str
    channel: str = ""


@dataclass(frozen=True)
class Snippet:
    text: str
    start: float
    duration: float


def search_youtube_interviews(
    queries: list[str],
    max_results_per_query: int = 10,
    strict_titles: bool = True,
) -> list[Video]:
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "skip_download": True,
    }

    videos: list[Video] = []
    seen_ids: set[str] = set()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for query in queries:
            search_keyword = f"ytsearch{max_results_per_query}:{query}"
            try:
                result = ydl.extract_info(search_keyword, download=False)
            except Exception as exc:
                print(f"Search failed for {query!r}: {exc}")
                continue

            for entry in result.get("entries", []):
                if not entry:
                    continue

                video_id = entry.get("id")
                title = entry.get("title") or ""
                if not video_id or video_id in seen_ids:
                    continue

                if strict_titles and not looks_like_lebron_interview(title):
                    continue

                seen_ids.add(video_id)
                videos.append(
                    Video(
                        video_id=video_id,
                        title=title,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        channel=entry.get("channel") or entry.get("uploader") or "",
                    )
                )
                print(f"Found: {title} ({video_id})")

    return videos


def looks_like_lebron_interview(title: str) -> bool:
    normalized = title.lower()
    mentions_lebron = "lebron" in normalized or "lebron james" in normalized
    has_interview_term = any(term in normalized for term in INTERVIEW_TERMS)
    has_skip_term = any(term in normalized for term in SKIP_TITLE_TERMS)
    return mentions_lebron and has_interview_term and not has_skip_term


def fetch_transcript(video_id: str, languages: tuple[str, ...] = ("en", "en-US")) -> list[Snippet]:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=languages)
    return [
        Snippet(
            text=item.text,
            start=float(item.start),
            duration=float(item.duration),
        )
        for item in transcript
    ]


def clean_caption_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\[(?:music|applause|laughter|cheering|inaudible).*?\]", " ", text, flags=re.I)
    text = re.sub(r"\((?:music|applause|laughter|cheering|inaudible).*?\)", " ", text, flags=re.I)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transcript_to_blocks(
    snippets: list[Snippet],
    min_words: int = 8,
    target_words: int = 45,
    max_words: int = 130,
    max_gap_seconds: float = 5.0,
) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    current_words = 0
    last_end: float | None = None

    for snippet in snippets:
        text = clean_caption_text(snippet.text)
        if not text:
            continue

        words = text.split()
        gap = snippet.start - last_end if last_end is not None else 0
        should_flush = bool(current) and (
            gap > max_gap_seconds
            or current_words >= max_words
            or (current_words >= target_words and sentence_ended(current[-1]))
        )

        if should_flush:
            add_block(blocks, " ".join(current), min_words)
            current = []
            current_words = 0

        current.append(text)
        current_words += len(words)
        last_end = snippet.start + snippet.duration

    if current:
        add_block(blocks, " ".join(current), min_words)

    return blocks


def sentence_ended(text: str) -> bool:
    return bool(re.search(r'[.!?]["\']?$', text))


def add_block(blocks: list[str], text: str, min_words: int) -> None:
    text = clean_training_block(text)
    if len(text.split()) < min_words:
        return
    if is_probably_non_lebron_text(text):
        return
    blocks.append(text)


def clean_training_block(text: str) -> str:
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_probably_non_lebron_text(text: str) -> bool:
    normalized = text.lower()
    if any(re.search(pattern, normalized) for pattern in SKIP_TEXT_PATTERNS):
        return True

    words = normalized.split()
    starts_like_reporter = bool(words) and words[0].strip(",.") in QUESTION_STARTERS
    has_first_person = bool(re.search(r"\b(i|i'm|i've|we|we're|we've|me|my|our|us)\b", normalized))

    if "?" in normalized and starts_like_reporter and not has_first_person:
        return True

    return False


def dedupe_blocks(blocks: list[str], existing_blocks: set[str] | None = None) -> list[str]:
    existing_blocks = existing_blocks or set()
    seen = set(existing_blocks)
    deduped: list[str] = []

    for block in blocks:
        key = normalize_for_dedupe(block)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(block)

    return deduped


def normalize_for_dedupe(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def read_existing_blocks(path: Path) -> set[str]:
    if not path.exists():
        return set()

    blocks = [block.strip() for block in path.read_text(encoding="utf-8").split("\n\n")]
    return {normalize_for_dedupe(block) for block in blocks if block}


def write_training_blocks(path: Path, blocks: list[str], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append and path.exists() else "w"
    prefix = "\n\n" if mode == "a" and path.stat().st_size else ""

    with path.open(mode, encoding="utf-8") as file:
        file.write(prefix + "\n\n".join(blocks))
        if blocks:
            file.write("\n")


def write_video_urls(path: Path, videos: list[Video]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{video.url}\t{video.title}" for video in videos]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def collect_lebron_quotes(
    queries: list[str],
    max_results_per_query: int,
    output_path: Path,
    urls_path: Path,
    append: bool,
    strict_titles: bool,
) -> int:
    videos = search_youtube_interviews(
        queries=queries,
        max_results_per_query=max_results_per_query,
        strict_titles=strict_titles,
    )
    write_video_urls(urls_path, videos)

    existing_blocks = read_existing_blocks(output_path) if append else set()
    all_blocks: list[str] = []

    for video in videos:
        print(f"Processing transcript: {video.title}")
        try:
            snippets = fetch_transcript(video.video_id)
        except Exception as exc:
            print(f"  Could not retrieve transcript for {video.video_id}: {exc}")
            continue

        blocks = transcript_to_blocks(snippets)
        blocks = dedupe_blocks(blocks, existing_blocks | {normalize_for_dedupe(block) for block in all_blocks})
        all_blocks.extend(blocks)
        print(f"  Added {len(blocks)} training blocks")

    write_training_blocks(output_path, all_blocks, append=append)
    return len(all_blocks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find LeBron interview videos and turn their transcripts into training text."
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="YouTube search query. Can be passed more than once.",
    )
    parser.add_argument("--max-results", type=int, default=8, help="Results to inspect per query.")
    parser.add_argument("--output", default="lebron_interview_quotes.txt", help="Training text output file.")
    parser.add_argument("--urls", default="lebron_interview_urls.txt", help="Video URL output file.")
    parser.add_argument("--append", action="store_true", help="Append unique blocks to the output file.")
    parser.add_argument(
        "--loose-titles",
        action="store_true",
        help="Keep more search results, even if the title does not strongly look like an interview.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    urls_path = Path(args.urls)
    queries = args.queries or DEFAULT_QUERIES

    added_count = collect_lebron_quotes(
        queries=queries,
        max_results_per_query=args.max_results,
        output_path=output_path,
        urls_path=urls_path,
        append=args.append,
        strict_titles=not args.loose_titles,
    )

    print(f"Saved {added_count} new training blocks to {output_path}")
    print(f"Saved searched video URLs to {urls_path}")


if __name__ == "__main__":
    main()
