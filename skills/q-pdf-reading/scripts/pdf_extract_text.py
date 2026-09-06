#!/usr/bin/env python3
"""Best-effort local PDF text extraction with only the Python standard library.

This is a fallback for simple digital PDFs when no PDF library is installed. It
does not replace PyMuPDF/Docling/Unstructured/OCR. It extracts decompressed text
operators and ToUnicode maps when they are easy to recover.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any
import zlib


OBJ_RE = re.compile(rb"(?m)(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", re.S)
STREAM_RE = re.compile(rb"(.*?)\bstream\r?\n(.*?)\r?\nendstream", re.S)
HEX_RE = re.compile(rb"<([0-9A-Fa-f\s]+)>")
LITERAL_RE = re.compile(rb"\((?:\\.|[^\\()])*\)", re.S)
TEXT_BLOCK_RE = re.compile(rb"BT\b(.*?)\bET", re.S)
TEXT_OP_RE = re.compile(
    rb"(\[(?:[^\[\]]|\\.)*?\]|<[^<>]*>|\((?:\\.|[^\\()])*\))\s*(?:Tj|TJ|'|\")",
    re.S,
)


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def decode_pdf_literal(token: bytes) -> bytes:
    body = token[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        b = body[i]
        if b != 0x5C:
            out.append(b)
            i += 1
            continue
        i += 1
        if i >= len(body):
            break
        esc = body[i]
        i += 1
        replacements = {
            ord("n"): ord("\n"),
            ord("r"): ord("\r"),
            ord("t"): ord("\t"),
            ord("b"): ord("\b"),
            ord("f"): ord("\f"),
            ord("("): ord("("),
            ord(")"): ord(")"),
            ord("\\"): ord("\\"),
        }
        if esc in replacements:
            out.append(replacements[esc])
        elif ord("0") <= esc <= ord("7"):
            digits = bytes([esc])
            for _ in range(2):
                if i < len(body) and ord("0") <= body[i] <= ord("7"):
                    digits += bytes([body[i]])
                    i += 1
                else:
                    break
            out.append(int(digits, 8) & 0xFF)
        elif esc in (ord("\r"), ord("\n")):
            if esc == ord("\r") and i < len(body) and body[i] == ord("\n"):
                i += 1
        else:
            out.append(esc)
    return bytes(out)


def decompress_stream(dict_part: bytes, stream_data: bytes) -> bytes | None:
    if b"/FlateDecode" not in dict_part:
        return None
    data = stream_data.strip(b"\r\n")
    for attempt in (
        lambda x: zlib.decompress(x),
        lambda x: zlib.decompress(x, -15),
        lambda x: zlib.decompressobj().decompress(x),
    ):
        try:
            return attempt(data)
        except Exception:
            continue
    return None


def extract_objects(pdf: bytes) -> dict[int, bytes]:
    objects: dict[int, bytes] = {}
    for match in OBJ_RE.finditer(pdf):
        objects[int(match.group(1))] = match.group(3)
    return objects


def extract_streams(objects: dict[int, bytes]) -> list[dict[str, Any]]:
    streams = []
    for obj_num, body in objects.items():
        match = STREAM_RE.search(body)
        if not match:
            continue
        decoded = decompress_stream(match.group(1), match.group(2))
        streams.append(
            {
                "object": obj_num,
                "dict": match.group(1),
                "decoded": decoded,
                "decoded_len": len(decoded) if decoded is not None else 0,
                "raw_len": len(match.group(2)),
            }
        )
    return streams


def parse_hex_bytes(raw: bytes) -> bytes:
    cleaned = re.sub(rb"\s+", b"", raw)
    if len(cleaned) % 2:
        cleaned += b"0"
    try:
        return bytes.fromhex(cleaned.decode("ascii"))
    except ValueError:
        return b""


def parse_unicode_value(hex_value: bytes) -> str:
    data = parse_hex_bytes(hex_value)
    if not data:
        return ""
    for encoding in ("utf-16-be", "utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def parse_cmaps(streams: list[dict[str, Any]]) -> dict[bytes, str]:
    cmap: dict[bytes, str] = {}
    for stream in streams:
        data = stream["decoded"]
        if not data or b"beginbf" not in data:
            continue
        for block in re.finditer(rb"beginbfchar(.*?)endbfchar", data, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
                key = parse_hex_bytes(src)
                value = parse_unicode_value(dst)
                if key and value:
                    cmap[key] = value
        for block in re.finditer(rb"beginbfrange(.*?)endbfrange", data, re.S):
            for src1, src2, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)):
                start = int(src1, 16)
                end = int(src2, 16)
                dst_start = int(dst, 16)
                width = max(len(src1), 2) // 2
                dst_width = max(len(dst), 4) // 2
                if end - start > 512:
                    continue
                for offset, code in enumerate(range(start, end + 1)):
                    key = code.to_bytes(width, "big")
                    value = (dst_start + offset).to_bytes(dst_width, "big").decode("utf-16-be", errors="ignore")
                    if value:
                        cmap[key] = value
            for src1, src2, array in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", block.group(1), re.S):
                start = int(src1, 16)
                width = max(len(src1), 2) // 2
                values = re.findall(rb"<([0-9A-Fa-f]+)>", array)
                for offset, dst in enumerate(values):
                    key = (start + offset).to_bytes(width, "big")
                    value = parse_unicode_value(dst)
                    if value:
                        cmap[key] = value
    return cmap


def decode_text_bytes(data: bytes, cmap: dict[bytes, str]) -> str:
    if not data:
        return ""
    if data.startswith(b"\xfe\xff"):
        return data[2:].decode("utf-16-be", errors="replace")
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le", errors="replace")
    if cmap:
        key_lengths = sorted({len(key) for key in cmap}, reverse=True)
        out = []
        i = 0
        while i < len(data):
            matched = False
            for length in key_lengths:
                chunk = data[i : i + length]
                if chunk in cmap:
                    out.append(cmap[chunk])
                    i += length
                    matched = True
                    break
            if not matched:
                b = data[i : i + 1]
                if 32 <= b[0] <= 126:
                    out.append(b.decode("latin-1"))
                i += 1
        return "".join(out)
    if b"\x00" in data:
        return data.decode("utf-16-be", errors="replace")
    return data.decode("utf-8", errors="replace")


def token_to_text(token: bytes, cmap: dict[bytes, str]) -> str:
    token = token.strip()
    if token.startswith(b"<") and token.endswith(b">"):
        return decode_text_bytes(parse_hex_bytes(token[1:-1]), cmap)
    if token.startswith(b"(") and token.endswith(b")"):
        return decode_text_bytes(decode_pdf_literal(token), cmap)
    if token.startswith(b"[") and token.endswith(b"]"):
        parts = []
        for literal in LITERAL_RE.findall(token):
            parts.append(decode_text_bytes(decode_pdf_literal(literal), cmap))
        for hex_match in HEX_RE.findall(token):
            parts.append(decode_text_bytes(parse_hex_bytes(hex_match), cmap))
        return "".join(parts)
    return ""


def clean_text(lines: list[str]) -> str:
    cleaned = []
    for line in lines:
        line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
        line = re.sub(r" +([,.;:!?，。；：！？）\]\}])", r"\1", line)
        line = re.sub(r"([（\[\{]) +", r"\1", line)
        if not line:
            continue
        if not re.search(r"[\w\u4e00-\u9fff]", line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_text_from_streams(streams: list[dict[str, Any]], cmap: dict[bytes, str]) -> tuple[str, list[dict[str, Any]]]:
    all_lines = []
    stream_notes = []
    for stream in streams:
        data = stream["decoded"]
        if not data or b"BT" not in data:
            continue
        lines = []
        for block in TEXT_BLOCK_RE.findall(data):
            block_lines = []
            for token in TEXT_OP_RE.findall(block):
                text = token_to_text(token, cmap)
                if text:
                    block_lines.append(text)
            if block_lines:
                lines.append(" ".join(block_lines))
        text = clean_text(lines)
        if text:
            all_lines.append(f"<!-- object {stream['object']} -->\n{text}")
            stream_notes.append({"object": stream["object"], "characters": len(text), "lines": text.count("\n") + 1})
    return "\n\n".join(all_lines), stream_notes


def estimate_page_count(pdf: bytes) -> int | None:
    page_count = len(re.findall(rb"/Type\s*/Page(?!s)\b", pdf))
    if page_count:
        return page_count
    counts = [int(match.group(1)) for match in re.finditer(rb"/Count\s+(\d+)", pdf)]
    return max(counts) if counts else None


def build_reading_notes(pdf: Path, text: str, streams: list[dict[str, Any]], cmap: dict[bytes, str], page_count: int | None) -> str:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    text_streams = [s for s in streams if s["decoded"] and b"BT" in s["decoded"]]
    warning = "This is a best-effort stdlib extraction. Validate against rendered pages or use a PDF library/OCR for final work."
    return "\n".join(
        [
            "# PDF Basic Extraction Notes",
            "",
            f"Created UTC: `{now}`",
            f"PDF: `{pdf.resolve()}`",
            f"Estimated pages: {page_count}",
            f"Decoded streams: {sum(1 for s in streams if s['decoded'])}/{len(streams)}",
            f"Text-like streams: {len(text_streams)}",
            f"ToUnicode entries: {len(cmap)}",
            f"Extracted characters: {len(text)}",
            "",
            f"Warning: {warning}",
            "",
            "Use this output as a quick local fallback, not as proof of full PDF comprehension.",
        ]
    )


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Best-effort PDF text extraction using only the standard library.")
    parser.add_argument("pdf", help="PDF file")
    parser.add_argument("--out", required=True, help="Output folder")
    args = parser.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pdf.read_bytes()
    objects = extract_objects(data)
    streams = extract_streams(objects)
    cmap = parse_cmaps(streams)
    text, stream_notes = extract_text_from_streams(streams, cmap)
    page_count = estimate_page_count(data)

    (out_dir / "extracted_text.md").write_text(text or "_No text extracted by stdlib fallback._\n", encoding="utf-8-sig")
    (out_dir / "basic_extraction_notes.md").write_text(build_reading_notes(pdf, text, streams, cmap, page_count), encoding="utf-8-sig")
    metadata = {
        "pdf": str(pdf.resolve()),
        "page_count_estimate": page_count,
        "object_count": len(objects),
        "stream_count": len(streams),
        "decoded_stream_count": sum(1 for s in streams if s["decoded"]),
        "text_stream_count": len(stream_notes),
        "to_unicode_entries": len(cmap),
        "extracted_characters": len(text),
        "stream_notes": stream_notes,
    }
    (out_dir / "basic_extraction.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    print(f"Wrote stdlib PDF extraction: {out_dir}")
    print(f"Extracted characters: {len(text)}")
    print(f"Text streams: {len(stream_notes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
