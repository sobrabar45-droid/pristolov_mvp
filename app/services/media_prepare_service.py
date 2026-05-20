from __future__ import annotations

import re
import shutil
from pathlib import Path

from app.services.question_import_service import build_questions_import_preview


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".jfif"}


def slugify_media_ref(text: str) -> str:
    value = str(text or "").strip().lower().replace("ё", "е")
    value = re.sub(r"^(фото|видео)\s+", "", value)
    value = re.sub(r"[«»\"'()]", " ", value)
    value = re.sub(r"[.,:!?]", " ", value)
    value = re.sub(r"[-\s]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def collect_media_refs_from_questions(file_path: str) -> list[str]:
    preview = build_questions_import_preview(file_path)
    refs: list[str] = []
    seen: set[str] = set()

    for item in preview.get("questions", []):
        media_ref = str(item.get("media_ref") or "").strip()
        if not item.get("is_media_question") or not media_ref:
            continue
        if media_ref in seen:
            continue
        seen.add(media_ref)
        refs.append(media_ref)

    return refs


def _iter_source_files(source_dir: Path) -> list[dict]:
    files: list[dict] = []
    for path in sorted(source_dir.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        files.append(
            {
                "path": path,
                "name": path.name,
                "extension": ext,
                "slug": slugify_media_ref(path.stem),
            }
        )
    return files


def _pick_best_candidates(media_slug: str, file_items: list[dict]) -> list[dict]:
    exact = [item for item in file_items if item["slug"] == media_slug]
    if exact:
        return exact

    fuzzy = [
        item
        for item in file_items
        if media_slug and item["slug"] and (media_slug in item["slug"] or item["slug"] in media_slug)
    ]
    if not fuzzy:
        return []

    shortest_len = min(len(item["slug"]) for item in fuzzy)
    return [item for item in fuzzy if len(item["slug"]) == shortest_len]


def prepare_media_files(
    source_dir: str,
    questions_file_path: str,
    dry_run: bool = True,
    force: bool = False,
) -> dict:
    source_path = Path(source_dir)
    media_refs = collect_media_refs_from_questions(questions_file_path)
    file_items = _iter_source_files(source_path)

    items: list[dict] = []
    missing: list[str] = []
    matched_count = 0
    copied_count = 0

    for media_ref in media_refs:
        media_slug = slugify_media_ref(media_ref)
        candidates = _pick_best_candidates(media_slug, file_items)
        warnings: list[str] = []

        if not candidates:
            items.append(
                {
                    "media_ref": media_ref,
                    "media_slug": media_slug,
                    "found_file": None,
                    "target_file": None,
                    "status": "missing",
                    "copied": False,
                    "warnings": [],
                    "ambiguous": False,
                    "candidates": [],
                }
            )
            missing.append(media_ref)
            continue

        chosen = candidates[0]
        ambiguous = len(candidates) > 1
        ext = chosen["extension"]
        target_name = f"{media_slug}{ext}"
        target_path = source_path / target_name

        if ext in {".jpeg", ".jfif"}:
            warnings.append("TV сейчас ожидает .jpg; файл надо конвертировать или расширить TV lookup")

        status = "matched"
        copied = False

        if not dry_run:
            same_file = chosen["path"].resolve() == target_path.resolve()
            if same_file:
                status = "exists"
            elif target_path.exists() and not force:
                status = "exists"
            else:
                shutil.copy2(chosen["path"], target_path)
                status = "copied"
                copied = True
                copied_count += 1

        matched_count += 1
        items.append(
            {
                "media_ref": media_ref,
                "media_slug": media_slug,
                "found_file": chosen["name"],
                "target_file": target_name,
                "status": status,
                "copied": copied,
                "warnings": warnings,
                "ambiguous": ambiguous,
                "candidates": [item["name"] for item in candidates],
            }
        )

    return {
        "ok": True,
        "dry_run": bool(dry_run),
        "force": bool(force),
        "questions_file_path": str(questions_file_path),
        "source_dir": str(source_path),
        "target_dir": str(source_path),
        "media_refs_count": len(media_refs),
        "matched_count": matched_count,
        "missing_count": len(missing),
        "copied_count": copied_count,
        "items": items,
        "missing": missing,
    }
