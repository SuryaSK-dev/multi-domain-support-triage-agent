import pytest
from src.retriever import Retriever, tokenize


@pytest.fixture(scope="module")
def retriever():
    return Retriever()


class TestTokenize:
    def test_lowercases_and_splits(self):
        assert tokenize("Hello World 123") == ["hello", "world", "123"]

    def test_empty_string(self):
        assert tokenize("") == []


class TestRetriever:
    def test_loads_corpus(self, retriever):
        assert len(retriever.chunks) > 0

    def test_relevant_query_beats_irrelevant(self, retriever):
        relevant = retriever.search("how do I delete my account", company="claude", k=1)
        irrelevant = retriever.search("asdkjhaskjdh random gibberish", k=1)
        relevant_conf = retriever.confidence(relevant, query="how do I delete my account")
        irrelevant_conf = retriever.confidence(irrelevant, query="asdkjhaskjdh random gibberish")
        assert relevant_conf > irrelevant_conf

    def test_company_filter_returns_matching_company(self, retriever):
        results = retriever.search("account settings", company="hackerrank", k=3)
        for chunk, score in results:
            assert chunk.company == "hackerrank"