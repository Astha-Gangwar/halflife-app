from backend.security.sensitive_content import looks_like_credential


def test_detects_plain_password_phrasing():
    assert looks_like_credential("my password is hunter2")
    assert looks_like_credential("Password: SuperSecret123!")
    assert looks_like_credential("pwd=letmein")


def test_detects_api_key_and_token_phrasing():
    assert looks_like_credential("api_key: abcdef12345")
    assert looks_like_credential("Here is my secret_key=xyz789")
    assert looks_like_credential("auth token is 9f8e7d6c5b")


def test_detects_known_credential_formats():
    assert looks_like_credential("AWS key AKIAABCDEFGHIJKLMNOP for the deploy user")
    assert looks_like_credential("sk-thisisaveryveryverylongfakesecretkey1234")
    fake_google_key = "AIza" + ("a" * 35)  # real Google API keys are AIza + 35 chars
    assert looks_like_credential(f"my google key is {fake_google_key}")


def test_does_not_flag_ordinary_content():
    assert not looks_like_credential("I want to try making sourdough bread this weekend")
    assert not looks_like_credential("Renew my passport before the trip")
    assert not looks_like_credential("")
    assert not looks_like_credential(None)


def test_does_not_flag_content_that_merely_mentions_the_word_password():
    # Discussing the concept of a password, without an actual value, is fine
    # to send for analysis; the heuristic requires an assignment-like pattern.
    assert not looks_like_credential("I should set up a password manager sometime")
