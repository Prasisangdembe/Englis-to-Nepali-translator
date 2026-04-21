def test_dictionary_translation_known_word(translation_service):
    result = translation_service.translate_word("hello")
    assert result["found"] is True
    assert result["limbu_romanized"] == "sewaro"
    assert result["limbu_script"] == "ᤛᤣᤘᤠᤖᤥ"


def test_dictionary_translation_unknown_word(translation_service):
    result = translation_service.translate_word("computer")
    assert result["found"] is False
    assert result["limbu_romanized"] == "[not found]"
    assert result["limbu_script"] == "[not found]"


def test_translation_methods_phrase_and_token_based(translation_service):
    phrase_result = translation_service.translate_text("thank you")
    assert phrase_result["translated_romanized"] == "khambe"
    assert phrase_result["found_all"] is True

    mixed_result = translation_service.translate_text("hello mountain")
    assert mixed_result["translated_romanized"] == "sewaro [mountain]"
    assert mixed_result["found_all"] is False
