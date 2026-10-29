from pathlib import Path

from google.cloud import storage


def download_content(
    bucket_name: str, dest: Path, client: storage.Client | None = None
) -> int:
    """Copies every object in the content bucket into dest, keeping its path.

    The bucket mirrors the repo layout (config/site.yaml, context/*.md), so after this call
    dest/config/site.yaml and dest/context/ can go straight to the usual local loaders.
    Returns how many files were downloaded. Errors (no bucket, no permission) propagate on
    purpose: a revision that can't read its content should fail to start, which leaves the
    previous revision serving on Cloud Run.
    """
    client = client or storage.Client()
    dest = dest.resolve()
    count = 0
    for blob in client.list_blobs(bucket_name):
        if blob.name.endswith("/"):  # folder placeholder objects
            continue
        target = (dest / blob.name).resolve()
        if not target.is_relative_to(dest):
            raise ValueError(f"Refusing to write {blob.name!r} outside {dest}")
        target.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(target))
        count += 1
    return count
