from sqlalchemy import text
from sqlalchemy.engine import Connection
from pathlib import Path

def validate_query(connection: Connection, query: str, check_name: str) -> None:
    """Execute a quality SELECT using the existing transaction connection.

    Raise ValueError identifying check_name if the query returns any row.
    Allow SQL errors to propagate without managing the transaction here.
    """
    query = query.strip()
    check_name = check_name.strip()  
    if not query:
        raise ValueError('Query is missing')
    if not check_name:
        raise ValueError('Check name is missing')
    statement = text(query)
    response = connection.execute(statement).first()
    if response is not None:
        raise ValueError(f'Query has returned values: {check_name}')

def read_checks(path: Path) -> list[tuple[str, str]]:
    """Read ordered (name, SQL) pairs from a UTF-8 file with '-- check:' markers.

    Allow blank lines before the first marker. Raise ValueError for unmarked
    content, empty or duplicate names, empty queries, or files without checks.
    File access errors propagate to the caller. Queries are not executed here.
    """
    def _validate_line(line: str, title: str | None) -> None:
        """Reject nonblank content before the first check marker."""
        if title is None and line.strip():
            raise ValueError('Content has been found before the first check')
        return
    def _extract_title(title: str, unique_titles: set[str]) -> str:
        """Extract a trimmed marker name, rejecting empty or previously seen names."""
        prefix = '-- check:'
        t = title.removeprefix(prefix).strip()
        if not t:
            raise ValueError('Missing title')
        if t in unique_titles:
            raise ValueError(f'Duplicated title is not allowed: {title}')
        return t
    def _format_query(query_lines: list[str], title: str) -> str:
        """Join and trim SQL lines, raising ValueError with the title if empty."""
        q = ''.join(query_lines).strip()
        if not q:
            raise ValueError(f'Empty query for {title}')
        return q
    results = []
    with open(file=path, mode="r", encoding="utf-8") as f:
        title = None
        unique_titles = set()
        query_lines = []
        prefix = '-- check:'
        for line in f:
            if line.startswith(prefix):
                if title is None:
                    title = _extract_title(line, unique_titles)
                    unique_titles.add(title)
                else:
                    query = _format_query(query_lines, title)
                    results.append((title, query))
                    title = _extract_title(line, unique_titles)
                    unique_titles.add(title)
                    query_lines.clear()
            else:
                _validate_line(line, title)
                query_lines.append(line)
        if title is not None:
            query = _format_query(query_lines, title)
            results.append((title, query))
        if not results:
            raise ValueError(f'Empty file: {path}')
        return results
            

            
        

