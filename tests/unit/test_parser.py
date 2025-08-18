from services.ingestion_service.parser.regex_parser import RegexParser

def test_regex_parser_basic():
    p = RegexParser()
    out = p.parse("2025-08-13 10:00:00 ERROR Connection refused")
    assert out["level"].lower().startswith("error")
    assert "Connection refused" in out["msg"]
