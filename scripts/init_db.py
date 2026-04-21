from sqlalchemy.exc import SQLAlchemyError

from config.database_config import Base, SessionLocal, engine
from models.feedback_model import Feedback, User, Validation  # noqa: F401
from models.translation_model import Dictionary, ParallelSentence, Translation  # noqa: F401
from utils.limbu_utils import LimbuScriptConverter


SEED_DICTIONARY = [
    ("hello", "sewaro"),
    ("water", "wa"),
    ("sun", "nam"),
    ("rice","tak"),
    ("eat","Kejabi"),
    ("kasko","Hal"),
    ("moon", "la"),
    ("thank you", "khambe"),
    ("earth", "him"),
    ("sky", "thak"),
    ("fire", "me"),
    ("wind", "sung"),
    ("mountain", "phung"),
    ("river", "khola"),
    ("tree", "sing"),
    ("flower", "fung"),
    ("leaf", "paat"),
    ("fruit", "sama"),
    ("rice", "chaam"),
    ("salt", "nun"),
    ("milk", "dudh"),
    ("dog", "khi"),
    ("cat", "biralo"),
    ("bird", "chara"),
    ("fish", "machha"),
    ("house", "yakthung"),
    ("road", "bato"),
    ("village", "gaun"),
    ("market", "haat"),
    ("book", "pustak"),
    ("school", "siksha"),
    ("teacher", "guru"),
    ("student", "bidyarthi"),
    ("friend", "mitra"),
    ("family", "pariwar"),
    ("father", "apa"),
    ("mother", "ama"),
    ("brother", "daju"),
    ("sister", "didi"),
    ("child", "keta"),
    ("man", "manche"),
    ("woman", "mahila"),
    ("day", "din"),
    ("night", "raat"),
    ("morning", "bihan"),
    ("evening", "beluka"),
    ("food", "khana"),
    ("work", "kam"),
    ("language", "bhasa"),
    ("name", "namu"),
    ("good", "ramro"),
    ("bad", "naramro"),
    ("yes", "ho"),
    ("no", "hoina"),
    ("come", "au"),
    ("go", "ja"),
    ("sit", "bas"),
    ("stand", "ubha"),
]

SEED_SENTENCES = [
    ("hello friend", "sewaro mitra"),
    ("thank you", "khambe"),
    ("the sun is bright", "nam ramro cha"),
    ("the moon is beautiful", "la ramro cha"),
    ("bring water", "wa lyaau"),
    ("we go to school", "hami siksha ja"),
    ("the child reads book", "keta pustak padhcha"),
    ("our village is peaceful", "hamro gaun shanta cha"),
    ("the bird flies", "chara uddcha"),
    ("food is ready", "khana tayari cha"),
]


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_dictionary(session) -> int:
    converter = LimbuScriptConverter()
    inserted = 0

    for english, romanized in SEED_DICTIONARY:
        exists = session.query(Dictionary).filter(Dictionary.english == english).first()
        if exists:
            continue

        entry = Dictionary(
            english=english,
            limbu=romanized,
            limbu_script=converter.romanized_to_script(romanized),
            pronunciation=converter.generate_pronunciation(romanized),
            verified=True,
        )
        session.add(entry)
        inserted += 1

    return inserted


def seed_sentences(session) -> int:
    converter = LimbuScriptConverter()
    inserted = 0

    for english, limbu in SEED_SENTENCES:
        exists = session.query(ParallelSentence).filter(ParallelSentence.english == english).first()
        if exists:
            continue

        sentence = ParallelSentence(
            english=english,
            limbu=limbu,
            limbu_script=converter.romanized_to_script(limbu),
            pronunciation=converter.generate_pronunciation(limbu),
            source="seed",
            verified=True,
        )
        session.add(sentence)
        inserted += 1

    return inserted


def main() -> None:
    print("Initializing database...")
    create_tables()

    session = SessionLocal()
    try:
        dictionary_count = seed_dictionary(session)
        sentence_count = seed_sentences(session)
        session.commit()
        print(f"Dictionary seed complete. Added {dictionary_count} entries.")
        print(f"Parallel sentence seed complete. Added {sentence_count} entries.")
        print("Database initialization completed successfully.")
    except SQLAlchemyError as exc:
        session.rollback()
        print(f"Database initialization failed: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
