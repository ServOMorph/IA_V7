from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_dom_ids_and_scripts_are_present():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    required_ids = {
        "panel-ia", "ia-btn-nouvelle-conv", "ia-btn-nouveau-dossier", "ia-ephemere",
        "ia-arbo", "ia-select-modele", "ia-statut-serveur", "ia-modele-charge",
        "ia-btn-serveur", "ia-btn-charger", "ia-btn-decharger", "ia-btn-defaut",
        "ia-titre-conv", "ia-messages", "ia-input", "ia-btn-envoyer", "ia-btn-stop",
        "ia-modal-help", "ia-btn-fermer-help", "ia-help-commandes",
    }
    for element_id in required_ids:
        assert f'id="{element_id}"' in html
    assert "chargerIA" in html
    assert "vendor/marked.umd.js" in html
    assert "vendor/purify.min.js" in html


def test_help_is_intercepted_by_the_interface():
    javascript = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "function iaOuvrirAide()" in javascript
    assert "texte.toLowerCase() === '/help'" in javascript
    assert "iaOuvrirAide();" in javascript


def test_serenia_visual_tokens_are_preserved():
    css = (ROOT / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert "--color-primary: rgb(165, 201, 202)" in css
    assert "--font-display: 'Space Grotesk'" in css
    assert ".ia-layout" in css
    assert "@media (prefers-color-scheme: dark)" in css
    assert "@media (max-width: 900px)" in css
