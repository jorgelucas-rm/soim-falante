"""
Script para importar arquivos de vocalização da pasta segments para o banco e MinIO.

Uso:
  python seed_vocalizations.py          # dry-run (apenas print)
  python seed_vocalizations.py --save   # grava no banco e no MinIO

Padrão do nome do arquivo:
  DD-MM-YYYY_Location_MainSpeaker_RecNum.Speaker[.SegmentNum].VocalizationType[.extra].wav

Exemplos:
  03-06-2023_Bosque_Abel_07.Abel.1.trill.wav
    → date=03/06/2023  location=Bosque  audio_number=07  speaker=Abel  segment=1  voc=trill

  03-06-2023_Bosque_Abel_05.unknow..trill..wav
    → segment ausente (campo vazio entre pontos)
"""

import io
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SEGMENTS_DIR = Path(__file__).parent / "segments"
SAVE_MODE = "--save" in sys.argv

VALID_VOCALIZATIONS = {
    "trill", "phee", "ek", "chirp", "chatter", "trillphee", "tsik", "twitter",
    "t-peep", "foodcall", "trill-foodcall", "peep",
}

VOCALIZATION_ALIASES = {
    "trill-phee": "trillphee",
    "trill phee": "trillphee",
}

_MINIO_PATH = "vocalizations"


@dataclass
class VocalizationRecord:
    file_name: str
    record_date: datetime
    location: str
    speaker: str
    vocalization: str
    audio_number: str | None
    segment: str | None
    comment: str | None


def normalize_speaker(raw: str) -> str:
    name = raw.strip().title()
    if name.lower() in ("unknow", "unknown"):
        return "Unknown"
    return name


def normalize_vocalization(raw: str) -> str | None:
    v = re.sub(r"\(\d+\)$", "", raw.strip()).strip()
    v = v.lower()
    v = VOCALIZATION_ALIASES.get(v, v)
    return v if v in VALID_VOCALIZATIONS else None


def sanitize_stem(stem: str) -> str:
    return re.sub(r"\.wav\s*\.", ".", stem, flags=re.IGNORECASE)


def parse_file_name(file_name: str) -> VocalizationRecord | None:
    stem = sanitize_stem(file_name.removesuffix(".wav"))

    dot_idx = stem.find(".")
    if dot_idx == -1:
        return None

    prefix = stem[:dot_idx]
    suffix = stem[dot_idx + 1:]

    parts = prefix.split("_")
    if len(parts) < 3:
        return None

    date_str = parts[0]
    location = parts[1]
    audio_number = parts[-1] if len(parts) >= 4 else None

    try:
        record_date = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return None

    suffix_parts = suffix.split(".")

    if len(suffix_parts) < 2:
        return None

    speaker_raw = suffix_parts[0]
    speaker = normalize_speaker(speaker_raw) if speaker_raw.strip() else "Unknown"

    if len(suffix_parts) >= 3 and re.fullmatch(r"\d*", suffix_parts[1].strip()):
        segment = suffix_parts[1].strip() or None
        vocalization_raw = suffix_parts[2]
        extra_parts = suffix_parts[3:]
    else:
        segment = None
        vocalization_raw = suffix_parts[1]
        extra_parts = suffix_parts[2:]

    vocalization = normalize_vocalization(vocalization_raw)
    if vocalization is None:
        return None

    comment = " ".join(p for p in extra_parts if p.strip()) or None

    return VocalizationRecord(
        file_name=file_name,
        record_date=record_date,
        location=location,
        speaker=speaker,
        vocalization=vocalization,
        audio_number=audio_number,
        segment=segment,
        comment=comment,
    )


def _build_object_name(file_name: str) -> str:
    return f"{_MINIO_PATH}/{file_name}"


def _upload_and_save(parsed: list[VocalizationRecord]) -> None:
    # Imports aqui para não quebrar o dry-run caso as dependências não estejam configuradas
    from minio import Minio
    from src.environments import (
        MINIO_DEFAULT_BUCKET,
        MINIO_HOST,
        MINIO_ROOT_PASSWORD,
        MINIO_ROOT_USER,
        MINIO_SECURE,
    )
    from src.infra.storage.database import session_maker
    from src.app.model.entity.vocalization import Vocalization

    minio = Minio(
        endpoint=MINIO_HOST,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=MINIO_SECURE.lower() == "true",
    )

    if not minio.bucket_exists(MINIO_DEFAULT_BUCKET):
        minio.make_bucket(MINIO_DEFAULT_BUCKET)
        print(f"Bucket '{MINIO_DEFAULT_BUCKET}' criado.")

    session = session_maker()
    saved = 0
    errors = 0

    try:
        for i, r in enumerate(parsed, 1):
            file_path = SEGMENTS_DIR / r.file_name
            object_name = _build_object_name(r.file_name)

            try:
                content = file_path.read_bytes()
                minio.put_object(
                    bucket_name=MINIO_DEFAULT_BUCKET,
                    object_name=object_name,
                    data=io.BytesIO(content),
                    length=len(content),
                    content_type="audio/wav",
                )

                entity = Vocalization(
                    speaker=r.speaker,
                    record_date=r.record_date,
                    location=r.location,
                    vocalization=r.vocalization,
                    audio_file=r.file_name,
                    audio_number=r.audio_number,
                    segment=r.segment,
                    comment=r.comment,
                )
                session.add(entity)

                if i % 50 == 0:
                    session.commit()
                    print(f"  {i}/{len(parsed)} gravados...")

                saved += 1

            except Exception as e:
                errors += 1
                print(f"  ERRO [{r.file_name}]: {e}")

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Erro fatal: {e}")
        raise
    finally:
        session.close()

    print(f"\nConcluído: {saved} gravados, {errors} erros.")


def main():
    files = sorted(f for f in os.listdir(SEGMENTS_DIR) if f.endswith(".wav"))
    parsed = [r for f in files if (r := parse_file_name(f))]
    skipped = len(files) - len(parsed)

    print(f"\n{'='*65}")
    print(f"Total de arquivos : {len(files)}")
    print(f"Identificados     : {len(parsed)}")
    print(f"Descartados       : {skipped}")
    print(f"Modo              : {'GRAVAÇÃO' if SAVE_MODE else 'DRY-RUN'}")
    print(f"{'='*65}\n")

    if not SAVE_MODE:
        print("=== AMOSTRA (primeiros 20) ===")
        for r in parsed[:20]:
            seg = r.segment or "-"
            rec = r.audio_number or "-"
            comment = f"  comment='{r.comment}'" if r.comment else ""
            print(
                f"  [{r.record_date.strftime('%d/%m/%Y')}] "
                f"loc={r.location:<10} rec={rec:<6} seg={seg:<4} "
                f"speaker={r.speaker:<14} voc={r.vocalization:<14}{comment}"
            )

        print("\n=== CONTAGEM POR VOCALIZAÇÃO ===")
        for voc, count in sorted(Counter(r.vocalization for r in parsed).items()):
            print(f"  {voc:<16}: {count}")

        print("\n=== CONTAGEM POR SPEAKER ===")
        for speaker, count in sorted(Counter(r.speaker for r in parsed).items()):
            print(f"  {speaker:<18}: {count}")

        with_seg = sum(1 for r in parsed if r.segment is not None)
        with_comment = sum(1 for r in parsed if r.comment is not None)
        print(f"\n  Com segment : {with_seg}")
        print(f"  Com comment : {with_comment}")
        print("\nPara gravar, execute: python seed_vocalizations.py --save")
    else:
        print(f"Iniciando upload de {len(parsed)} arquivos para MinIO e banco...\n")
        _upload_and_save(parsed)


if __name__ == "__main__":
    main()
