import os
from pathlib import Path
import pandas as pd
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("bible-rag")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

TRANSLATION = "KJV" 


NT_BOOKS = {
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation"
}

GENRE_MAP: dict[str, list[str]] = {
    "Gospel": ["Matthew", "Mark", "Luke", "John"],
    "Epistle": [
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
        "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
        "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
        "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude",
    ],
    "Torah": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
    "Prophecy": [
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
        "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
        "Malachi", "Revelation",
    ],
}

def get_genre(book_name: str) -> str:
    """Return genre via exact book name match (not substring, to avoid collisions)."""
    for genre, books in GENRE_MAP.items():
        if book_name in books:
            return genre
    return "History/Wisdom/Other"


def flush_batch(batch_records: list) -> None:
    """Embed and upsert a batch of (id, text, metadata) tuples."""
    if not batch_records:
        return
    ids, texts, metas = zip(*batch_records)
    vectors = embeddings.embed_documents(list(texts))
    to_upsert = [
        {"id": id_, "values": vec, "metadata": meta}
        for id_, vec, meta in zip(ids, vectors, metas)
    ]
    index.upsert(vectors=to_upsert)

def ingest_bible(file_path: str | None = None, batch_size: int = 100) -> None:
    """
    Ingest the KJV Bible into Pinecone using a sliding window per chapter.

    Chunking strategy:
      - window_size=3: each chunk is 3 consecutive verses
      - step_size=1:   stride of 1 verse (high overlap for better retrieval recall)
      - Windows are scoped to a single chapter to avoid cross-chapter context bleed.
    """
    base = Path(__file__).resolve().parent
    csv_path = Path(file_path) if file_path else base / "kjv-bible.csv"
    df = pd.read_csv(csv_path)  # Expected columns: Book, Chapter, Verse, Text

    window_size = 3
    step_size = 1
    batch_records: list[tuple] = []
    total_upserted = 0

    for book in df["Book"].unique():
        book_df = df[df["Book"] == book]
        genre = get_genre(book)
        testament = "New" if book in NT_BOOKS else "Old"

        # ── Scope windows to individual chapters to prevent context bleed ──
        for chapter in book_df["Chapter"].unique():
            chap_df = book_df[book_df["Chapter"] == chapter].reset_index(drop=True)
            n = len(chap_df)

            # For very short chapters (< window_size), emit a single chunk.
            effective_range = range(0, max(1, n - window_size + 1), step_size)

            for i in effective_range:
                window = chap_df.iloc[i : i + window_size]

                start_verse = int(window.iloc[0]["Verse"])
                end_verse = int(window.iloc[-1]["Verse"])

                # Human-readable reference label embedded in the text chunk.
                ref_label = f"{book} {chapter}:{start_verse}-{end_verse}"
                combined_text = " ".join(window["Text"].tolist())
                full_content = f"{ref_label}: {combined_text}"

                # Stable, content-addressable ID — survives re-runs and config changes.
                chunk_id = f"{TRANSLATION}-{book}-{chapter}-{start_verse}-{end_verse}"

                metadata = {
                    "translation": TRANSLATION,
                    "reference": ref_label,
                    "book": book,
                    "chapter": int(chapter),
                    "start_verse": start_verse,
                    "end_verse": end_verse,
                    "testament": testament,
                    "genre": genre,
                    "text": combined_text,
                }

                batch_records.append((chunk_id, full_content, metadata))

                if len(batch_records) >= batch_size:
                    flush_batch(batch_records)
                    total_upserted += len(batch_records)
                    print(f"Upserted {total_upserted} chunks | last: {ref_label}")
                    batch_records = []

    if batch_records:
        flush_batch(batch_records)
        total_upserted += len(batch_records)
        print(f"Flushed final batch | total upserted: {total_upserted}")

    print(f"\nIngestion complete. Total chunks upserted: {total_upserted}")


if __name__ == "__main__":
    ingest_bible()