from ia_v7.services.context import (
    build_context,
    build_sliding_context,
    extract_facts_regex,
    format_facts,
    parse_llm_facts,
)


def test_extract_facts_regex():
    facts = extract_facts_regex("Je m'appelle Raphaël et j'utilise Ollama")
    assert {fact["fait"] for fact in facts} == {"Raphaël", "Ollama"}


def test_parse_llm_facts():
    raw = 'Réponse : {"faits": [{"categorie": "projet", "fait": "IA V7"}]}'
    assert parse_llm_facts(raw)[0]["fait"] == "IA V7"
    assert parse_llm_facts("pas de JSON") == []


def test_context_contains_system_facts_history_and_user():
    context = build_context(
        "Sois bref",
        [{"role": "user", "contenu": "Ancien"}, {"role": "assistant", "contenu": "Réponse"}],
        "Nouveau",
        [{"categorie": "outil", "fait": "Ollama"}],
        16384,
    )
    assert context[0]["role"] == "system"
    assert "Ollama" in context[0]["content"]
    assert context[-1] == {"role": "user", "content": "Nouveau"}
    assert len(context) == 4


def test_sliding_context_respects_tiny_budget():
    context = build_sliding_context(
        "système",
        [{"role": "user", "contenu": "x" * 1000}, {"role": "assistant", "contenu": "y" * 1000}],
        "question",
        num_ctx=2100,
    )
    assert [message["role"] for message in context] == ["system", "user"]


def test_format_facts_empty_and_populated():
    assert format_facts([]) == ""
    assert format_facts([{"categorie": None, "fait": "Valeur"}]) == "[Contexte de la conversation]\n- info: Valeur"

