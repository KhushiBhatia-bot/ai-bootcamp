def chunk_pages(
    pages,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
):
    """
    Split page text into overlapping chunks while
    preserving the original page number.
    """

    chunks = []

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "page": page_number,
                    }
                )

            start += chunk_size - chunk_overlap

    return chunks