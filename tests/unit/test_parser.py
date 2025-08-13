import pytest
from services.ingestion_service.parser.regex_parser import RegexParser

def test_regex_parser_extracts_errors():
    log = "[2025-08-12 10:00:00] ERROR Something went wrong"
    parser = RegexParser()
    result = parser.parse(log)
    assert len(result) == 1
    assert result[0]['level'] == 'ERROR'
