import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any


TEXT_EXTS = {
    ".html", ".htm", ".css", ".js", ".ts", ".json", ".xml", ".svg",
    ".md", ".txt", ".py"
}

BINARY_OR_SKIP_EXTS = {
    ".woff", ".woff2", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".webp", ".ico"
}

WEB_EXTS = {
    ".html", ".htm", ".css", ".js", ".json", ".xml", ".svg", ".md", ".txt"
}


def is_text_file(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext in BINARY_OR_SKIP_EXTS:
        return False
    if ext in TEXT_EXTS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(2048)
        if b"\0" in chunk:
            return False
    except Exception:
        return False
    return True


def safe_read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
    except Exception:
        return None


def safe_write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def normalize_str_separators(p: str) -> str:
    return p.replace("\\", "/")


def strip_known_schemes(p: str) -> str:
    lower = p.lower()
    if lower.startswith("file://"):
        p = p.split("file://", 1)[1]
    return p


def is_url_like(p: str) -> bool:
    lower = p.lower().strip()
    return lower.startswith("http://") or lower.startswith("https://") or lower.startswith("data:") or lower.startswith("mailto:") or lower.startswith("tel:")


def find_candidates(content: str) -> List[Tuple[int, int, str]]:
    candidates: List[Tuple[int, int, str]] = []
    patterns = [
        r"([\"'])(?P<path>(?:[A-Za-z]:[\\/]|\\\\)[^\"']+)(\1)",
        r"url\(\s*(?P<url>(?:[A-Za-z]:[\\/]|\\\\)[^\s)\"']+|/(?!/)[^\s)\"']+)\s*\)",
        r"([\"'])(?P<posix>/(?!/)[^\"']+)(\1)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, content):
            s, e = m.span()
            grp = m.groupdict()
            raw = grp.get("path") or grp.get("url") or grp.get("posix")
            if raw:
                candidates.append((s, e, raw))
    return candidates


def path_in_root_from_string(raw: str, root: Path) -> Optional[Path]:
    if is_url_like(raw):
        return None
    raw = strip_known_schemes(raw)
    norm_raw = normalize_str_separators(raw)
    root_norm = normalize_str_separators(str(root.resolve()))

    if norm_raw.lower().startswith(root_norm.lower() + "/") or norm_raw.lower() == root_norm.lower():
        rel = norm_raw[len(root_norm):].lstrip("/")
        target = root / rel
        if target.exists():
            return target.resolve()
        return None

    try:
        p = Path(raw)
        if p.is_absolute() and p.exists():
            p_res = p.resolve()
            try:
                _ = p_res.relative_to(root.resolve())
                return p_res
            except Exception:
                return None
    except Exception:
        pass
    return None


def relpath_for_file(target_abs: Path, file_dir: Path, ext: str) -> str:
    rel = os.path.relpath(str(target_abs), str(file_dir))
    if ext.lower() in WEB_EXTS:
        rel = normalize_str_separators(rel)
    return rel


def replace_candidates(content: str, file_path: Path, root: Path) -> Tuple[str, List[Dict[str, Any]]]:
    changes: List[Dict[str, Any]] = []
    candidates = find_candidates(content)
    if not candidates:
        return content, changes

    by_index: Dict[int, Tuple[int, int, str]] = {i: c for i, c in enumerate(candidates)}
    new_content = content
    offset = 0
    for idx in range(len(by_index)):
        s, e, raw = by_index[idx]
        s += offset
        e += offset
        target = path_in_root_from_string(raw, root)
        if not target:
            continue
        ext = file_path.suffix.lower()
        file_dir = file_path.parent
        new_rel = relpath_for_file(target, file_dir, ext)
        before = new_content[:s]
        middle = new_content[s:e]
        after = new_content[e:]
        middle = middle.replace(raw, new_rel)
        updated = before + middle + after
        offset = len(updated) - len(new_content)
        new_content = updated
        line_num = new_content.count("\n", 0, s) + 1
        changes.append({
            "file": str(file_path),
            "line": line_num,
            "original": raw,
            "replacement": new_rel,
            "target_abs": str(target)
        })
    return new_content, changes


def join_prefix(prefix: str, path: str) -> str:
    if not prefix:
        return path
    pfx = prefix[:-1] if prefix.endswith('/') else prefix
    return pfx + path


def replace_webroot_refs(content: str, file_path: Path, web_root_prefix: Optional[str]) -> Tuple[str, List[Dict[str, Any]]]:
    changes: List[Dict[str, Any]] = []
    if not web_root_prefix:
        return content, changes

    def hrefsrc_repl(m: re.Match) -> str:
        attr = m.group('attr')
        quote = m.group('quote')
        path = m.group('path')
        if is_url_like(path) or path.startswith('//') or path.startswith('/books/'):
            return m.group(0)
        newp = join_prefix(web_root_prefix, path)
        changes.append({
            "file": str(file_path),
            "line": content.count('\n', 0, m.start()) + 1,
            "original": path,
            "replacement": newp,
            "kind": "webroot_prefix"
        })
        return f"{attr}={quote}{newp}{quote}"

    new_content = re.sub(r"(?P<attr>(?:href|src))\s*=\s*(?P<quote>[\"'])(?P<path>/(?!/)[^\"']+)(?P=quote)", hrefsrc_repl, content)

    def url_repl(m: re.Match) -> str:
        quote = m.group('quote') or ''
        path = m.group('path')
        if path.startswith('//'):
            return m.group(0)
        newp = join_prefix(web_root_prefix, path)
        changes.append({
            "file": str(file_path),
            "line": new_content.count('\n', 0, m.start()) + 1,
            "original": path,
            "replacement": newp,
            "kind": "webroot_prefix_css"
        })
        return f"url({quote}{newp}{quote})"

    newer_content = re.sub(r"url\(\s*(?P<quote>[\"']?)(?P<path>/(?!/)[^\)\"']+)(?P=quote)\s*\)", url_repl, new_content)
    return newer_content, changes


def ensure_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)


def collect_files(root: Path) -> List[Path]:
    files: List[Path] = []
    skip_dirs = {root / "_path_conversion", root / "_backup_before_path_conversion"}
    for p in root.rglob("*"):
        if any(str(p).startswith(str(sd)) for sd in skip_dirs):
            continue
        if p.is_file() and is_text_file(p):
            files.append(p)
    return files


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def backup_file(file_path: Path, backup_root: Path) -> Path:
    dst = backup_root / file_path.relative_to(backup_root.parent)
    ensure_dir(dst.parent)
    if not dst.exists():
        dst.write_bytes(file_path.read_bytes())
    return dst


def clean_ref(ref: str) -> str:
    ref = ref.strip().strip('"').strip("'")
    ref = ref.split('#')[0].split('?')[0]
    return ref


def find_web_refs(content: str) -> List[str]:
    refs: List[str] = []
    for m in re.finditer(r"(?:href|src)\s*=\s*([\"'])([^\"']+)(\1)", content, flags=re.IGNORECASE):
        refs.append(m.group(2))
    for m in re.finditer(r"url\(\s*([^\)]+)\s*\)", content, flags=re.IGNORECASE):
        refs.append(m.group(1).strip().strip('"').strip("'"))
    return refs


def verify(root: Path, files: List[Path], log_dir: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"root": str(root), "files": {}, "missing_total": 0}
    for f in files:
        ext = f.suffix.lower()
        # Limit verification to HTML and CSS to avoid false positives in minified JS
        if ext not in {".html", ".htm", ".css"}:
            continue
        content = safe_read_text(f)
        if content is None:
            continue
        refs = find_web_refs(content)
        missing: List[str] = []
        for r in refs:
            if is_url_like(r):
                continue
            r_clean = clean_ref(r)
            if not r_clean:
                continue
            if r_clean.startswith("//"):
                continue
            candidate: Optional[Path] = None
            if r_clean.startswith("/"):
                candidate = root / r_clean.lstrip("/")
            else:
                candidate = f.parent / normalize_str_separators(r_clean)
            try:
                exists = candidate.exists()
            except Exception:
                exists = False
            if not exists:
                missing.append(r)
        if missing:
            result["files"][str(f)] = missing
            result["missing_total"] += len(missing)
    write_json(log_dir / "verification.json", result)
    (log_dir / "verification.txt").write_text(
        f"Root: {result['root']}\nFiles with missing refs: {len(result['files'])}\nMissing refs total: {result['missing_total']}\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert absolute filesystem paths to relative paths within a root")
    ap.add_argument("--root", required=True, help="Root directory (books) to operate on")
    ap.add_argument("--dry-run", action="store_true", help="Only analyze and report changes, do not modify files")
    ap.add_argument("--execute", action="store_true", help="Perform modifications with backup and logging")
    ap.add_argument("--rollback", action="store_true", help="Rollback changes by restoring from backup")
    ap.add_argument("--verify", action="store_true", help="Run link/reference verification and write report")
    ap.add_argument("--web-root-prefix", default=None, help="Rewrite web-root absolute refs ('/') to prefix, e.g., /books")
    ap.add_argument("--log-dir", default=None, help="Directory to store logs (default: <root>/_path_conversion)")
    ap.add_argument("--backup-dir", default=None, help="Directory to store backups (default: <root>/_backup_before_path_conversion)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Root not found: {root}")
        return 2

    log_dir = Path(args.log_dir) if args.log_dir else (root / "_path_conversion")
    backup_dir = Path(args.backup_dir) if args.backup_dir else (root / "_backup_before_path_conversion")
    ensure_dir(log_dir)
    ensure_dir(backup_dir)

    if args.rollback:
        restored = 0
        for src in backup_dir.rglob("*"):
            if src.is_file():
                dst = root / src.relative_to(backup_dir)
                ensure_dir(dst.parent)
                dst.write_bytes(src.read_bytes())
                restored += 1
        print(f"Rollback completed. Restored {restored} files from {backup_dir}")
        return 0

    files = collect_files(root)
    analysis: Dict[str, Any] = {"root": str(root), "files_count": len(files), "changes": []}

    for f in files:
        content = safe_read_text(f)
        if content is None:
            continue
        new_content, changes = replace_candidates(content, f, root)
        wr_content, wr_changes = replace_webroot_refs(new_content, f, args.web_root_prefix)
        new_content = wr_content
        if wr_changes:
            analysis["changes"].extend(wr_changes)
        if changes:
            analysis["changes"].extend(changes)
        if (changes or wr_changes) and args.execute and not args.dry_run:
            backup_file(f, backup_dir)
            safe_write_text(f, new_content)

    from datetime import datetime
    summary = {
        "root": str(root),
        "files_scanned": len(files),
        "changes_total": len(analysis["changes"]),
        "time": datetime.now().isoformat()
    }

    write_json(log_dir / ("precheck.json" if args.dry_run or not args.execute else "conversion.json"), analysis)
    (log_dir / ("precheck.txt" if args.dry_run or not args.execute else "conversion.txt")).write_text(
        f"Root: {summary['root']}\nFiles scanned: {summary['files_scanned']}\nChanges total: {summary['changes_total']}\n",
        encoding="utf-8",
    )

    if args.verify:
        verify(root, files, log_dir)

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

