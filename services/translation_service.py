import json
import logging
import re
from difflib import get_close_matches
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from config.database_config import redis_client
except Exception:  # pragma: no cover - fallback when Redis is unavailable
    redis_client = None


class TranslationService:
    """English to Limbu translation service with cache and fallback layers."""

    CACHE_PREFIX = "translation_service"
    CACHE_TTL_SECONDS = 3600
    FUZZY_CUTOFF = 0.75
    MAX_PHRASE_LENGTH = 4

    def __init__(self) -> None:
        self.dictionary = self._load_dictionary()
        self.common_phrases = self._load_common_phrases()

    def _load_dictionary(self) -> Dict[str, Dict[str, str]]:
        """Load seed dictionary entries."""
        return {
            "hello": {"romanized": "sewaro", "script": "ᤛᤣᤘᤠᤖᤥ"},
            "water": {"romanized": "wa", "script": "ᤘᤠ"},
            "sun": {"romanized": "nam", "script": "ᤏᤠᤔ"},
            "moon": {"romanized": "la", "script": "ᤗᤠ"},
            "thank you": {"romanized": "khambe", "script": "ᤂᤠᤔᤒᤣ"},
        }

    def _load_common_phrases(self) -> Dict[str, Dict[str, str]]:
        """Load phrase/sentence-level translations."""
        return {
            "how are you": {"romanized": "khene hangba", "script": "ᤂᤣᤏᤣ ᤛᤠᤑ᤺ᤠ"},
            "good morning": {"romanized": "subha bihan", "script": "ᤚᤢᤘᤠ ᤒᤡᤛᤠᤏ"},
            "good night": {"romanized": "subha raat", "script": "ᤚᤢᤘᤠ ᤖᤠᤋ"},
            "see you again": {"romanized": "pheri bhetaula", "script": "ᤑᤣᤖᤡ ᤒᤣᤋᤠᤢᤗᤠ"},
            "what is your name": {"romanized": "nangga namu ke", "script": "ᤏᤠᤅᤁᤠ ᤏᤠᤔᤢ ᤁᤣ"},
        }

    def add_translation(self, english: str, romanized: str, script: str = "") -> None:
        """Add or update a dictionary entry."""
        normalized = self._normalize_text(english)
        self.dictionary[normalized] = {
            "romanized": romanized.strip(),
            "script": script.strip(),
        }
        self._cache_delete(f"word:{normalized}")

    def translate_word(self, english: str) -> Dict[str, object]:
        """Translate a single word or phrase with exact/fuzzy/ML fallback."""
        try:
            normalized = self._normalize_text(english)
            cache_key = f"word:{normalized}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

            entry = self._lookup_exact(normalized)
            method = "dictionary"
            matched_source = normalized

            if not entry:
                fuzzy_key = self._fuzzy_match(normalized)
                if fuzzy_key:
                    entry = self._lookup_exact(fuzzy_key)
                    method = "fuzzy"
                    matched_source = fuzzy_key

            if not entry:
                ml_entry = self._ml_predict(normalized)
                if ml_entry:
                    entry = ml_entry
                    method = "ml_stub"
                    matched_source = normalized

            if not entry:
                result = {
                    "english": english,
                    "limbu_romanized": "[not found]",
                    "limbu_script": "[not found]",
                    "found": False,
                    "method": "none",
                }
            else:
                result = {
                    "english": english,
                    "limbu_romanized": entry["romanized"],
                    "limbu_script": entry["script"] or "[not available]",
                    "found": True,
                    "method": method,
                }
                if matched_source != normalized:
                    result["matched_input"] = matched_source

            self._cache_set(cache_key, result)
            return result
        except Exception as exc:
            logger.exception("translate_word failed for input '%s': %s", english, exc)
            return {
                "english": english,
                "limbu_romanized": "[error]",
                "limbu_script": "[error]",
                "found": False,
                "method": "error",
            }

    def translate_text(self, text: str) -> Dict[str, object]:
        """
        Translate English text with phrase/sentence support.

        Matching order:
        1) Exact phrase/sentence in common phrases or dictionary
        2) Longest phrase matching (up to MAX_PHRASE_LENGTH tokens)
        3) Single token lookup with fuzzy/ML fallback
        """
        try:
            normalized_text = self._normalize_text(text)
            cache_key = f"text:{normalized_text}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

            direct_entry = self._lookup_exact(normalized_text)
            if direct_entry:
                result = {
                    "original_text": text,
                    "translated_romanized": direct_entry["romanized"],
                    "translated_script": direct_entry["script"] or "[not available]",
                    "found_all": True,
                    "tokens": [self.translate_word(text)],
                    "method": "exact_phrase",
                }
                self._cache_set(cache_key, result)
                return result

            tokens = self._tokenize(text)
            translated_romanized: List[str] = []
            translated_script: List[str] = []
            token_results: List[Dict[str, object]] = []

            i = 0
            found_all = True
            while i < len(tokens):
                match_found = False
                max_span = min(self.MAX_PHRASE_LENGTH, len(tokens) - i)

                for span in range(max_span, 0, -1):
                    candidate = " ".join(tokens[i : i + span])
                    candidate_result = self.translate_word(candidate)
                    if candidate_result["found"]:
                        translated_romanized.append(candidate_result["limbu_romanized"])
                        translated_script.append(candidate_result["limbu_script"])
                        token_results.append(candidate_result)
                        i += span
                        match_found = True
                        break

                if not match_found:
                    # This branch should rarely occur due to translate_word fallback behavior.
                    found_all = False
                    unknown = tokens[i]
                    token_results.append(
                        {
                            "english": unknown,
                            "limbu_romanized": "[not found]",
                            "limbu_script": "[not found]",
                            "found": False,
                            "method": "none",
                        }
                    )
                    translated_romanized.append(f"[{unknown}]")
                    translated_script.append(f"[{unknown}]")
                    i += 1
                elif not token_results[-1]["found"]:
                    found_all = False

            result = {
                "original_text": text,
                "translated_romanized": " ".join(translated_romanized),
                "translated_script": " ".join(translated_script),
                "found_all": found_all,
                "tokens": token_results,
                "method": "hybrid",
            }
            self._cache_set(cache_key, result)
            return result
        except Exception as exc:
            logger.exception("translate_text failed for input '%s': %s", text, exc)
            return {
                "original_text": text,
                "translated_romanized": "[error]",
                "translated_script": "[error]",
                "found_all": False,
                "tokens": [],
                "method": "error",
            }

    def _lookup_exact(self, normalized: str) -> Optional[Dict[str, str]]:
        if normalized in self.common_phrases:
            return self.common_phrases[normalized]
        return self.dictionary.get(normalized)

    def _fuzzy_match(self, normalized: str) -> Optional[str]:
        search_space = list(self.common_phrases.keys()) + list(self.dictionary.keys())
        matches = get_close_matches(normalized, search_space, n=1, cutoff=self.FUZZY_CUTOFF)
        return matches[0] if matches else None

    def _ml_predict(self, normalized: str) -> Optional[Dict[str, str]]:
        """
        Basic ML inference stub for future integration.

        Return None for now; future models can return:
        {"romanized": "...", "script": "..."}.
        """
        _ = normalized
        return None

    def _cache_get(self, key: str) -> Optional[Dict[str, object]]:
        if redis_client is None:
            return None
        try:
            raw = redis_client.get(f"{self.CACHE_PREFIX}:{key}")
            if not raw:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Cache get failed for key '%s': %s", key, exc)
            return None

    def _cache_set(self, key: str, value: Dict[str, object]) -> None:
        if redis_client is None:
            return
        try:
            redis_client.setex(
                f"{self.CACHE_PREFIX}:{key}",
                self.CACHE_TTL_SECONDS,
                json.dumps(value, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning("Cache set failed for key '%s': %s", key, exc)

    def _cache_delete(self, key: str) -> None:
        if redis_client is None:
            return
        try:
            redis_client.delete(f"{self.CACHE_PREFIX}:{key}")
        except Exception as exc:
            logger.warning("Cache delete failed for key '%s': %s", key, exc)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Keep letters and apostrophes, drop punctuation.
        return re.findall(r"[a-zA-Z']+", text.lower())
