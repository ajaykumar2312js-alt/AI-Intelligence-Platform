from pathlib import Path


async def extract_content(file_path: Path, content_type: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".txt" or suffix == ".md":
        return _read_text(file_path)
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    if suffix in (".docx", ".doc"):
        return _extract_docx(file_path)
    if suffix in (".html", ".htm"):
        return _extract_html(file_path)
    if suffix == ".csv":
        return _extract_csv(file_path)

    return _read_text(file_path)


def _read_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(file_path: Path) -> str:
    try:
        from unstructured.partition.pdf import partition_pdf
        elements = partition_pdf(filename=str(file_path))
        return "\n\n".join(str(el) for el in elements)
    except ImportError:
        raise ImportError("Install 'unstructured' for PDF support: pip install unstructured")


def _extract_docx(file_path: Path) -> str:
    try:
        from unstructured.partition.docx import partition_docx
        elements = partition_docx(filename=str(file_path))
        return "\n\n".join(str(el) for el in elements)
    except ImportError:
        raise ImportError("Install 'unstructured' for DOCX support: pip install unstructured")


def _extract_html(file_path: Path) -> str:
    try:
        from unstructured.partition.html import partition_html
        elements = partition_html(filename=str(file_path))
        return "\n\n".join(str(el) for el in elements)
    except ImportError:
        raise ImportError("Install 'unstructured' for HTML support: pip install unstructured")


def _extract_csv(file_path: Path) -> str:
    import csv
    with open(file_path, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        return "\n".join(",".join(row) for row in reader)
