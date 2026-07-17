let iaConvCourante = null;
let iaController = null;
let iaModeles = [];
let iaInitialise = false;
let iaStatutTimer = null;
let iaCommandes = [];
let iaSuggestionIndex = -1;
const iaDossiersOuverts = new Set();
const iaClickTimers = {};
const iaLivrables = new Map();
let iaLivrableSeq = 0;

function iaEsc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function iaCopierPressePapier(texte) {
    return new Promise((resolve) => {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(texte)
                .then(() => resolve(true))
                .catch(() => resolve(iaCopierFallback(texte)));
        } else {
            resolve(iaCopierFallback(texte));
        }
    });
}

function iaCopierFallback(texte) {
    const ta = document.createElement('textarea');
    ta.value = texte;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    ta.style.pointerEvents = 'none';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
}

function iaLivrableFormat(texte) {
    const t = texte.trim();
    if (/^<!DOCTYPE|^<html/i.test(t)) return { ext: 'html', mime: 'text/html' };
    try { JSON.parse(t); return { ext: 'json', mime: 'application/json' }; } catch (e) {}
    if (/^#{1,6} |\n#{1,6} |\*\*[^*]|\n- /.test(t)) return { ext: 'md', mime: 'text/markdown' };
    return { ext: 'txt', mime: 'text/plain' };
}

function iaLivrableCopier(id) {
    const texte = iaLivrables.get(id);
    if (!texte) return;
    iaCopierPressePapier(texte).then(() => {
        const btn = document.querySelector(`.ia-livrable[data-id="${id}"] .ia-livrable-btn-copier`);
        if (btn) { btn.textContent = 'Copié ✓'; setTimeout(() => { btn.textContent = 'Copier'; }, 1500); }
    });
}

function iaLivrableTelechargement(id) {
    const texte = iaLivrables.get(id);
    if (!texte) return;
    const { ext, mime } = iaLivrableFormat(texte);
    const blob = new Blob([texte], { type: mime + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'livrable.' + ext;
    a.click();
    URL.revokeObjectURL(url);
}

function iaRendu(contenu) {
    if (typeof marked !== 'undefined' && marked.parse) {
        try {
            const renderer = new marked.Renderer();
            const base = new marked.Renderer();
            renderer.code = function(tokenOrCode, lang) {
                let code, language;
                if (tokenOrCode && typeof tokenOrCode === 'object' && 'text' in tokenOrCode) {
                    code = tokenOrCode.text || '';
                    language = tokenOrCode.lang || '';
                } else {
                    code = tokenOrCode || '';
                    language = lang || '';
                }
                if (language === 'livrable') {
                    const id = 'lv-' + (++iaLivrableSeq);
                    iaLivrables.set(id, code);
                    const corps = iaEsc(code).replace(/\n/g, '<br>');
                    return `<div class="ia-livrable" data-id="${id}">` +
                        `<div class="ia-livrable-barre">` +
                        `<span class="ia-livrable-label">Livrable</span>` +
                        `<button class="ia-livrable-btn ia-livrable-btn-copier" data-action="copier" data-livrable-id="${id}">Copier</button>` +
                        `<button class="ia-livrable-btn" data-action="telecharger" data-livrable-id="${id}">⬇ Télécharger</button>` +
                        `</div>` +
                        `<div class="ia-livrable-corps">${corps}</div>` +
                        `</div>`;
                }
                if (typeof base.code === 'function') return base.code.call(this, tokenOrCode, lang);
                return `<pre><code>${iaEsc(code)}</code></pre>`;
            };
            const html = marked.parse(contenu, { renderer });
            return typeof DOMPurify !== 'undefined'
                ? DOMPurify.sanitize(html)
                : iaEsc(contenu).replace(/\n/g, '<br>');
        } catch (e) { /* fallback */ }
    }
    return iaEsc(contenu).replace(/\n/g, '<br>');
}

function iaBrancherLivrables(racine) {
    racine.querySelectorAll('.ia-livrable-btn[data-action]').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.livrableId;
            if (btn.dataset.action === 'copier') iaLivrableCopier(id);
            if (btn.dataset.action === 'telecharger') iaLivrableTelechargement(id);
        };
    });
}

async function iaFetchJSON(url, options) {
    const r = await fetch(url, options);
    let data = null;
    try { data = await r.json(); } catch (e) { data = null; }
    return { ok: r.ok, status: r.status, data };
}

// --- Statut serveur & modèles -------------------------------------------

async function iaMajStatut() {
    const pastille = document.getElementById('ia-statut-serveur');
    const btnServeur = document.getElementById('ia-btn-serveur');
    try {
        const { data } = await iaFetchJSON('/api/ia/statut');
        const actif = data && data.serveur;
        const modeles = (data && data.modeles_charges) || [];
        pastille.style.background = actif ? 'var(--color-success)' : 'var(--color-error)';
        pastille.title = actif ? 'Serveur Ollama actif' : 'Serveur Ollama arrêté';
        btnServeur.textContent = actif ? 'Arrêter serveur' : 'Démarrer serveur';
        btnServeur.dataset.actif = actif ? '1' : '0';
        const modeleChargeEl = document.getElementById('ia-modele-charge');
        if (modeleChargeEl) {
            const charge = modeles.length > 0;
            modeleChargeEl.textContent = charge ? '● ' + modeles[0] : '○ aucun modèle chargé';
            modeleChargeEl.classList.toggle('ia-modele-charge-vide', !charge);
            modeleChargeEl.title = charge ? 'Modèle chargé en mémoire' : 'Aucun modèle chargé — le 1er message déclenchera un chargement (1-2 min)';
        }
        window.iaModelesCharges = modeles;
    } catch (e) {
        pastille.style.background = 'var(--color-error)';
    }
}

async function iaChargerModeles() {
    const select = document.getElementById('ia-select-modele');
    const { ok, data } = await iaFetchJSON('/api/ia/modeles');
    iaModeles = (ok && data && data.modeles) ? data.modeles : [];
    const courant = iaConvCourante ? iaConvCourante.modele : null;
    select.innerHTML = iaModeles.map(m =>
        `<option value="${iaEsc(m)}" ${m === courant ? 'selected' : ''}>${iaEsc(m)}</option>`).join('');
    if (!iaModeles.length) {
        select.innerHTML = '<option value="">(Ollama injoignable)</option>';
    }
}

// --- Commandes / suggestions ---------------------------------------------

async function iaChargerCommandes() {
    const { ok, data } = await iaFetchJSON('/api/ia/commandes');
    iaCommandes = (ok && Array.isArray(data)) ? data : [];
}

function iaMasquerSuggestions() {
    const boite = document.getElementById('ia-suggestions');
    boite.style.display = 'none';
    boite.innerHTML = '';
    iaSuggestionIndex = -1;
}

function iaAfficherSuggestions(filtre) {
    const boite = document.getElementById('ia-suggestions');
    const correspondances = iaCommandes.filter(c => c.nom.startsWith(filtre));
    if (!correspondances.length) {
        iaMasquerSuggestions();
        return;
    }
    boite.innerHTML = correspondances.map((c, i) =>
        `<div class="ia-suggestion" data-nom="${iaEsc(c.nom)}" data-index="${i}">` +
        `<strong>/${iaEsc(c.nom)}</strong><span>${iaEsc(c.description)}</span></div>`
    ).join('');
    boite.style.display = 'block';
    iaSuggestionIndex = -1;
    boite.querySelectorAll('.ia-suggestion').forEach(el => {
        el.onmousedown = (e) => {
            e.preventDefault();
            iaChoisirSuggestion(el.dataset.nom);
        };
    });
}

function iaChoisirSuggestion(nom) {
    const input = document.getElementById('ia-input');
    input.value = '/' + nom + ' ';
    iaMasquerSuggestions();
    input.focus();
}

function iaGererSaisieCommande() {
    const input = document.getElementById('ia-input');
    const valeur = input.value;
    const match = /^\/(\w*)$/.exec(valeur);
    if (match) {
        iaAfficherSuggestions(match[1].toLowerCase());
    } else {
        iaMasquerSuggestions();
    }
}

function iaNaviguerSuggestions(e) {
    const boite = document.getElementById('ia-suggestions');
    if (boite.style.display === 'none') return false;
    const items = Array.from(boite.querySelectorAll('.ia-suggestion'));
    if (!items.length) return false;
    if (e.key === 'ArrowDown') {
        iaSuggestionIndex = (iaSuggestionIndex + 1) % items.length;
    } else if (e.key === 'ArrowUp') {
        iaSuggestionIndex = (iaSuggestionIndex - 1 + items.length) % items.length;
    } else if (e.key === 'Tab' || e.key === 'Enter') {
        const cible = items[iaSuggestionIndex] || items[0];
        iaChoisirSuggestion(cible.dataset.nom);
        return true;
    } else if (e.key === 'Escape') {
        iaMasquerSuggestions();
        return true;
    } else {
        return false;
    }
    items.forEach(el => el.classList.remove('ia-suggestion-active'));
    items[iaSuggestionIndex].classList.add('ia-suggestion-active');
    return true;
}

// --- Arborescence dossiers / conversations ------------------------------

async function iaChargerArbo() {
    const [dRes, cRes] = await Promise.all([
        iaFetchJSON('/api/ia/dossiers'),
        iaFetchJSON('/api/ia/conversations'),
    ]);
    const dossiers = dRes.data || [];
    const convs = cRes.data || [];
    const arbo = document.getElementById('ia-arbo');

    const sansDossier = convs.filter(c => c.dossier_id == null && !c.ephemere);
    let html = '';

    for (const d of dossiers) {
        const ouvert = iaDossiersOuverts.has(d.id);
        const convsD = convs.filter(c => c.dossier_id === d.id && !c.ephemere);
        html += `<div class="ia-dossier" data-id="${d.id}">
            <div class="ia-dossier-tete">
                <span class="ia-dossier-toggle" data-id="${d.id}">${ouvert ? '▾' : '▸'}</span>
                <span class="ia-dossier-nom" data-id="${d.id}" title="Double-clic pour renommer">${iaEsc(d.nom)}</span>
                <button class="ia-icon-btn ia-dossier-nouvelle-conv" data-id="${d.id}" title="Nouvelle conversation dans ce dossier">+</button>
                <button class="ia-icon-btn ia-dossier-prompt" data-id="${d.id}" title="System prompt">⚙</button>
                <button class="ia-icon-btn ia-dossier-suppr" data-id="${d.id}" title="Supprimer">✕</button>
            </div>
            <div class="ia-dossier-prompt-zone" data-id="${d.id}" style="display:none;">
                <textarea class="ia-prompt-input" data-id="${d.id}" placeholder="System prompt du dossier…">${iaEsc(d.system_prompt)}</textarea>
                <button class="ia-btn-mini ia-prompt-save" data-id="${d.id}">Enregistrer</button>
            </div>
            <div class="ia-dossier-convs" style="display:${ouvert ? 'block' : 'none'};">
                ${convsD.map(c => iaConvLigne(c)).join('') || '<div class="ia-vide">vide</div>'}
            </div>
        </div>`;
    }

    html += `<div class="ia-racine">
        ${sansDossier.map(c => iaConvLigne(c)).join('')}
    </div>`;

    arbo.innerHTML = html;
    iaBrancherArbo();
}

function iaConvLigne(c) {
    const actif = iaConvCourante && iaConvCourante.id === c.id ? ' ia-conv-actif' : '';
    const titre = c.titre && c.titre.trim() ? c.titre : 'Sans titre';
    return `<div class="ia-conv${actif}" data-id="${c.id}">
        <span class="ia-conv-nom" data-id="${c.id}" title="Double-clic pour renommer">${iaEsc(titre)}</span>
        <button class="ia-icon-btn ia-conv-suppr" data-id="${c.id}" title="Supprimer">✕</button>
    </div>`;
}

function iaBrancherArbo() {
    document.querySelectorAll('.ia-dossier-toggle').forEach(el => {
        el.onclick = () => {
            const id = +el.dataset.id;
            if (iaDossiersOuverts.has(id)) iaDossiersOuverts.delete(id);
            else iaDossiersOuverts.add(id);
            iaChargerArbo();
        };
    });
    document.querySelectorAll('.ia-conv-nom').forEach(el => {
        const id = +el.dataset.id;
        el.onclick = () => {
            clearTimeout(iaClickTimers[id]);
            iaClickTimers[id] = setTimeout(() => iaOuvrirConversation(id), 220);
        };
        el.ondblclick = (e) => {
            e.stopPropagation();
            clearTimeout(iaClickTimers[id]);
            iaRenommerInline(el, 'conv', id);
        };
    });
    document.querySelectorAll('.ia-dossier-nom').forEach(el => {
        el.ondblclick = (e) => { e.stopPropagation(); iaRenommerInline(el, 'dossier', +el.dataset.id); };
    });
    document.querySelectorAll('.ia-dossier-nouvelle-conv').forEach(el => {
        el.onclick = (e) => { e.stopPropagation(); iaNouvelleConversationDansDossier(+el.dataset.id); };
    });
    document.querySelectorAll('.ia-conv-suppr').forEach(el => {
        el.onclick = (e) => { e.stopPropagation(); iaSupprimerConv(+el.dataset.id); };
    });
    document.querySelectorAll('.ia-dossier-suppr').forEach(el => {
        el.onclick = (e) => { e.stopPropagation(); iaSupprimerDossier(+el.dataset.id); };
    });
    document.querySelectorAll('.ia-dossier-prompt').forEach(el => {
        el.onclick = () => {
            const zone = document.querySelector(`.ia-dossier-prompt-zone[data-id="${el.dataset.id}"]`);
            zone.style.display = zone.style.display === 'none' ? 'block' : 'none';
        };
    });
    document.querySelectorAll('.ia-prompt-save').forEach(el => {
        el.onclick = async () => {
            const ta = document.querySelector(`.ia-prompt-input[data-id="${el.dataset.id}"]`);
            await iaFetchJSON(`/api/ia/dossiers/${el.dataset.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: ta.value }),
            });
            el.textContent = 'Enregistré ✓';
            setTimeout(() => {
                el.textContent = 'Enregistrer';
                const zone = document.querySelector(`.ia-dossier-prompt-zone[data-id="${el.dataset.id}"]`);
                if (zone) zone.style.display = 'none';
            }, 900);
        };
    });
}

function iaRenommerInline(el, type, id) {
    const ancien = el.textContent === 'Sans titre' ? '' : el.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = ancien;
    input.className = 'ia-rename-input';
    el.replaceWith(input);
    input.focus();
    input.select();
    const valider = async () => {
        const nv = input.value.trim();
        const url = type === 'conv' ? `/api/ia/conversations/${id}` : `/api/ia/dossiers/${id}`;
        const champ = type === 'conv' ? 'titre' : 'nom';
        if (nv && nv !== ancien) {
            await iaFetchJSON(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [champ]: nv }),
            });
            if (type === 'conv' && iaConvCourante && iaConvCourante.id === id) {
                iaConvCourante.titre = nv;
                document.getElementById('ia-titre-conv').textContent = nv;
            }
        }
        iaChargerArbo();
    };
    input.onblur = valider;
    input.onkeydown = (e) => {
        if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
        if (e.key === 'Escape') { iaChargerArbo(); }
    };
}

async function iaSupprimerConv(id) {
    if (!confirm('Supprimer cette conversation ?')) return;
    await iaFetchJSON(`/api/ia/conversations/${id}`, { method: 'DELETE' });
    if (iaConvCourante && iaConvCourante.id === id) {
        iaConvCourante = null;
        document.getElementById('ia-messages').innerHTML = '';
        document.getElementById('ia-titre-conv').textContent = '';
    }
    iaChargerArbo();
}

async function iaSupprimerDossier(id) {
    if (!confirm('Supprimer ce dossier et toutes ses conversations ?')) return;
    await iaFetchJSON(`/api/ia/dossiers/${id}`, { method: 'DELETE' });
    iaChargerArbo();
}

// --- Création -----------------------------------------------------------

async function iaNouveauDossier() {
    const nom = prompt('Nom du dossier :');
    if (!nom || !nom.trim()) return;
    await iaFetchJSON('/api/ia/dossiers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom: nom.trim() }),
    });
    iaChargerArbo();
}

async function iaNouvelleConversationDansDossier(dossierId) {
    const ephemere = document.getElementById('ia-ephemere').checked;
    const modele = document.getElementById('ia-select-modele').value;
    const { data } = await iaFetchJSON('/api/ia/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modele, ephemere, dossier_id: dossierId }),
    });
    if (data) {
        iaConvCourante = data;
        iaDossiersOuverts.add(dossierId);
        document.getElementById('ia-messages').innerHTML = ephemere
            ? '<div class="ia-info">Conversation éphémère (non sauvegardée)</div>' : '';
        document.getElementById('ia-titre-conv').textContent = ephemere ? 'Éphémère' : 'Nouvelle conversation';
        iaChargerArbo();
    }
}

async function iaNouvelleConversation() {
    const ephemere = document.getElementById('ia-ephemere').checked;
    const modele = document.getElementById('ia-select-modele').value;
    const { data } = await iaFetchJSON('/api/ia/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modele, ephemere }),
    });
    if (data) {
        iaConvCourante = data;
        document.getElementById('ia-messages').innerHTML = ephemere
            ? '<div class="ia-info">Conversation éphémère (non sauvegardée)</div>' : '';
        document.getElementById('ia-titre-conv').textContent = ephemere ? 'Éphémère' : 'Nouvelle conversation';
        iaChargerArbo();
    }
}

// --- Ouverture conversation & messages ----------------------------------

async function iaOuvrirConversation(id) {
    const { data } = await iaFetchJSON(`/api/ia/conversations/${id}`);
    if (!data) return;
    iaConvCourante = data;
    document.getElementById('ia-titre-conv').textContent =
        (data.titre && data.titre.trim()) ? data.titre : 'Sans titre';
    const select = document.getElementById('ia-select-modele');
    if (data.modele && iaModeles.includes(data.modele)) select.value = data.modele;
    const zone = document.getElementById('ia-messages');
    zone.innerHTML = '';
    (data.messages || []).forEach(m => iaAjouterBulle(m.role, m.contenu));
    iaScrollBas();
    iaChargerArbo();
}

function iaAjouterBulle(role, contenu) {
    const zone = document.getElementById('ia-messages');
    const bulle = document.createElement('div');
    bulle.className = 'ia-bulle ia-bulle-' + role;
    bulle.iaContenu = contenu;
    const corps = document.createElement('div');
    corps.className = 'ia-bulle-corps';
    corps.innerHTML = role === 'assistant' ? iaRendu(contenu) : iaEsc(contenu).replace(/\n/g, '<br>');
    if (role === 'assistant') iaBrancherLivrables(corps);
    const copier = document.createElement('button');
    copier.className = 'ia-copier';
    copier.textContent = 'Copier';
    copier.onclick = () => {
        iaCopierPressePapier(bulle.iaContenu).then(() => {
            copier.textContent = 'Copié ✓';
            setTimeout(() => { copier.textContent = 'Copier'; }, 1500);
        });
    };
    bulle.appendChild(corps);
    bulle.appendChild(copier);
    zone.appendChild(bulle);
    return corps;
}

function iaAjouterMarqueurModele(modele) {
    const zone = document.getElementById('ia-messages');
    const sep = document.createElement('div');
    sep.className = 'ia-marqueur-modele';
    sep.textContent = 'Modèle : ' + modele;
    zone.appendChild(sep);
    iaScrollBas();
}

function iaScrollBas() {
    const zone = document.getElementById('ia-messages');
    zone.scrollTop = zone.scrollHeight;
}

// --- Envoi & streaming --------------------------------------------------

async function iaEnvoyer() {
    const input = document.getElementById('ia-input');
    const texte = input.value.trim();
    if (!texte) return;
    iaMasquerSuggestions();

    if (!iaConvCourante) {
        await iaNouvelleConversation();
        if (!iaConvCourante) return;
    }

    const premierEchange = !(iaConvCourante.titre && iaConvCourante.titre.trim());
    const estCommande = texte.startsWith('/');

    input.value = '';
    input.style.height = 'auto';
    iaAjouterBulle('user', texte);
    const corpsIA = iaAjouterBulle('assistant', '');
    if (estCommande) corpsIA.parentElement.classList.add('ia-bulle-commande');
    const modeleConv = iaConvCourante.modele || document.getElementById('ia-select-modele').value;
    const modeleCharge = (window.iaModelesCharges || []).includes(modeleConv);
    const pointsHTML = '<span class="ia-attente"><span></span><span></span><span></span></span>';
    corpsIA.innerHTML = (estCommande || modeleCharge)
        ? pointsHTML
        : '<span class="ia-chargement-modele">Chargement du modèle en mémoire… (1 à 2 min au premier message)</span> ' + pointsHTML;
    iaScrollBas();
    iaBasculerGeneration(true);

    iaController = new AbortController();
    let accumule = '';
    try {
        const r = await fetch(`/api/ia/conversations/${iaConvCourante.id}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: texte }),
            signal: iaController.signal,
        });
        const reader = r.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const blocs = buffer.split('\n\n');
            buffer = blocs.pop();
            for (const bloc of blocs) {
                const ligne = bloc.trim();
                if (!ligne.startsWith('data:')) continue;
                let obj;
                try { obj = JSON.parse(ligne.slice(5).trim()); } catch (e) { continue; }
                if (obj.contenu) {
                    accumule += obj.contenu;
                    corpsIA.parentElement.iaContenu = accumule;
                    if (estCommande) {
                        corpsIA.innerHTML = iaEsc(accumule).replace(/\n/g, '<br>');
                    } else {
                        corpsIA.innerHTML = iaRendu(accumule);
                        iaBrancherLivrables(corpsIA);
                    }
                    iaScrollBas();
                } else if (obj.erreur) {
                    if (estCommande) corpsIA.parentElement.classList.add('ia-bulle-commande-erreur');
                    corpsIA.innerHTML = '<span style="color:var(--color-error);">Erreur : ' + iaEsc(obj.erreur) + '</span>';
                }
            }
        }
    } catch (e) {
        if (e.name !== 'AbortError') {
            corpsIA.innerHTML = '<span style="color:var(--color-error);">Erreur réseau : ' + iaEsc(e.message) + '</span>';
        }
    } finally {
        iaBasculerGeneration(false);
        iaController = null;
        if (!accumule.trim() && corpsIA.querySelector('.ia-attente')) {
            corpsIA.innerHTML = '<span style="color:var(--color-text-muted);">(aucune réponse)</span>';
        }
    }

    if (premierEchange && !iaConvCourante.ephemere && accumule.trim() && !estCommande) {
        const { data } = await iaFetchJSON(`/api/ia/conversations/${iaConvCourante.id}/titre-auto`, { method: 'POST' });
        if (data && data.titre) {
            iaConvCourante.titre = data.titre;
            document.getElementById('ia-titre-conv').textContent = data.titre;
        }
        iaChargerArbo();
    }
}

function iaBasculerGeneration(enCours) {
    document.getElementById('ia-btn-envoyer').style.display = enCours ? 'none' : '';
    document.getElementById('ia-btn-stop').style.display = enCours ? '' : 'none';
    document.getElementById('ia-input').disabled = enCours;
}

function iaStop() {
    if (iaController) iaController.abort();
}

// --- Pilotage serveur / modèle ------------------------------------------

async function iaToggleServeur() {
    const btn = document.getElementById('ia-btn-serveur');
    const actif = btn.dataset.actif === '1';
    btn.disabled = true;
    btn.textContent = actif ? 'Serveur en cours d\'arrêt…' : 'Serveur en cours de démarrage…';
    try {
        await iaFetchJSON(actif ? '/api/ia/serveur/stop' : '/api/ia/serveur/start', { method: 'POST' });
    } catch (e) { /* on sonde le statut ci-dessous de toute façon */ }
    const cible = !actif;
    for (let i = 0; i < 20; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const { data } = await iaFetchJSON('/api/ia/statut');
        if (data && !!data.serveur === cible) break;
    }
    await iaMajStatut();
    await iaChargerModeles();
    btn.disabled = false;
}

async function iaChargerModeleCourant() {
    const modele = document.getElementById('ia-select-modele').value;
    if (!modele) return;
    const btn = document.getElementById('ia-btn-charger');
    btn.disabled = true;
    btn.textContent = 'Chargement…';
    await iaFetchJSON('/api/ia/modele/charger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modele }),
    });
    btn.textContent = 'Charger modèle';
    btn.disabled = false;
    iaMajStatut();
}

async function iaDechargerModeleCourant() {
    const modele = document.getElementById('ia-select-modele').value;
    if (!modele) return;
    await iaFetchJSON('/api/ia/modele/decharger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modele }),
    });
    iaMajStatut();
}

async function iaDefinirModelDefault() {
    const modele = document.getElementById('ia-select-modele').value;
    if (!modele) return;
    const btn = document.getElementById('ia-btn-defaut');
    btn.disabled = true;
    const { ok } = await iaFetchJSON('/api/ia/modele/defaut', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modele }),
    });
    if (ok) {
        btn.textContent = 'Défaut ✓';
        setTimeout(() => { btn.textContent = 'Défaut'; btn.disabled = false; }, 1500);
    } else {
        btn.disabled = false;
    }
}

// --- Capture d'écran ----------------------------------------------------

let iaCaptureEtat = null;

function iaCaptureToast(message, erreur) {
    const toast = document.createElement('div');
    toast.className = 'ia-capture-toast' + (erreur ? ' ia-capture-toast-erreur' : '');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

function iaCaptureDemarrer() {
    if (iaCaptureEtat) return;
    const overlay = document.createElement('div');
    overlay.id = 'ia-capture-overlay';
    overlay.innerHTML =
        '<div class="ia-capture-aide">Tracez un rectangle à la souris, ajustez-le, puis validez.</div>' +
        '<div id="ia-capture-rect" style="display:none;">' +
        ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'].map(d =>
            `<span class="ia-capture-poignee ia-capture-poignee-${d}" data-dir="${d}"></span>`).join('') +
        '</div>' +
        '<div id="ia-capture-actions" style="display:none;">' +
        '<button id="ia-capture-valider" class="ia-btn-primary">Valider</button>' +
        '<button id="ia-capture-annuler" class="ia-btn-mini">Annuler</button>' +
        '</div>';
    document.body.appendChild(overlay);
    iaCaptureEtat = { overlay, rect: null, drag: null };

    overlay.onmousedown = (e) => {
        if (e.target.closest('#ia-capture-actions')) return;
        const poignee = e.target.closest('.ia-capture-poignee');
        const rectEl = document.getElementById('ia-capture-rect');
        if (poignee) {
            iaCaptureEtat.drag = { mode: 'resize', dir: poignee.dataset.dir, x: e.clientX, y: e.clientY, base: { ...iaCaptureEtat.rect } };
        } else if (e.target === rectEl) {
            iaCaptureEtat.drag = { mode: 'move', x: e.clientX, y: e.clientY, base: { ...iaCaptureEtat.rect } };
        } else {
            iaCaptureEtat.rect = { x: e.clientX, y: e.clientY, w: 0, h: 0 };
            iaCaptureEtat.drag = { mode: 'draw', x: e.clientX, y: e.clientY };
        }
        e.preventDefault();
    };
    overlay.onmousemove = (e) => {
        const etat = iaCaptureEtat;
        if (!etat || !etat.drag) return;
        const dx = e.clientX - etat.drag.x;
        const dy = e.clientY - etat.drag.y;
        if (etat.drag.mode === 'draw') {
            etat.rect = {
                x: Math.min(etat.drag.x, e.clientX),
                y: Math.min(etat.drag.y, e.clientY),
                w: Math.abs(dx),
                h: Math.abs(dy),
            };
        } else if (etat.drag.mode === 'move') {
            etat.rect = { ...etat.drag.base, x: etat.drag.base.x + dx, y: etat.drag.base.y + dy };
        } else {
            const b = etat.drag.base;
            const dir = etat.drag.dir;
            let { x, y, w, h } = b;
            if (dir.includes('w')) { x = b.x + dx; w = b.w - dx; }
            if (dir.includes('e')) { w = b.w + dx; }
            if (dir.includes('n')) { y = b.y + dy; h = b.h - dy; }
            if (dir.includes('s')) { h = b.h + dy; }
            if (w < 0) { x += w; w = -w; }
            if (h < 0) { y += h; h = -h; }
            etat.rect = { x, y, w, h };
        }
        iaCaptureAfficherRect();
    };
    overlay.onmouseup = () => {
        if (!iaCaptureEtat || !iaCaptureEtat.drag) return;
        const dessin = iaCaptureEtat.drag.mode === 'draw';
        iaCaptureEtat.drag = null;
        if (dessin && (!iaCaptureEtat.rect || iaCaptureEtat.rect.w < 5 || iaCaptureEtat.rect.h < 5)) {
            iaCaptureEtat.rect = null;
            iaCaptureAfficherRect();
        }
    };
    document.getElementById('ia-capture-valider').onclick = iaCaptureValider;
    document.getElementById('ia-capture-annuler').onclick = iaCaptureFermer;
    iaCaptureEtat.echap = (e) => { if (e.key === 'Escape') iaCaptureFermer(); };
    document.addEventListener('keydown', iaCaptureEtat.echap);
}

function iaCaptureAfficherRect() {
    const etat = iaCaptureEtat;
    if (!etat) return;
    const rectEl = document.getElementById('ia-capture-rect');
    const actions = document.getElementById('ia-capture-actions');
    if (!etat.rect) {
        rectEl.style.display = 'none';
        actions.style.display = 'none';
        return;
    }
    rectEl.style.display = 'block';
    rectEl.style.left = etat.rect.x + 'px';
    rectEl.style.top = etat.rect.y + 'px';
    rectEl.style.width = etat.rect.w + 'px';
    rectEl.style.height = etat.rect.h + 'px';
    actions.style.display = 'flex';
    const sousRect = etat.rect.y + etat.rect.h + 46;
    actions.style.top = Math.min(sousRect, window.innerHeight - 46) + 'px';
    actions.style.left = Math.max(etat.rect.x, 8) + 'px';
}

function iaCaptureFermer() {
    if (!iaCaptureEtat) return;
    document.removeEventListener('keydown', iaCaptureEtat.echap);
    iaCaptureEtat.overlay.remove();
    iaCaptureEtat = null;
}

async function iaCaptureValider() {
    const etat = iaCaptureEtat;
    if (!etat || !etat.rect || etat.rect.w < 5 || etat.rect.h < 5) return;
    const zone = { ...etat.rect };
    iaCaptureFermer();
    if (typeof html2canvas === 'undefined') {
        iaCaptureToast('html2canvas indisponible', true);
        return;
    }
    try {
        const canvas = await html2canvas(document.body, {
            x: zone.x + window.scrollX,
            y: zone.y + window.scrollY,
            width: zone.w,
            height: zone.h,
            logging: false,
        });
        const image = canvas.toDataURL('image/png');
        const { ok, data } = await iaFetchJSON('/api/ia/captures', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image }),
        });
        if (ok && data && data.fichier) {
            iaCaptureToast('Capture enregistrée : ' + data.fichier);
        } else {
            iaCaptureToast('Erreur : ' + ((data && data.error) || 'enregistrement impossible'), true);
        }
    } catch (e) {
        iaCaptureToast('Erreur de capture : ' + e.message, true);
    }
}

// --- Initialisation -----------------------------------------------------

function iaBrancherUI() {
    if (iaInitialise) return;
    iaInitialise = true;
    document.getElementById('ia-btn-nouvelle-conv').onclick = iaNouvelleConversation;
    document.getElementById('ia-btn-nouveau-dossier').onclick = iaNouveauDossier;
    document.getElementById('ia-btn-envoyer').onclick = iaEnvoyer;
    document.getElementById('ia-btn-stop').onclick = iaStop;
    document.getElementById('ia-btn-serveur').onclick = iaToggleServeur;
    document.getElementById('ia-btn-charger').onclick = iaChargerModeleCourant;
    document.getElementById('ia-btn-decharger').onclick = iaDechargerModeleCourant;
    document.getElementById('ia-btn-defaut').onclick = iaDefinirModelDefault;
    document.getElementById('ia-btn-capture').onclick = iaCaptureDemarrer;

    const input = document.getElementById('ia-input');
    input.onkeydown = (e) => {
        if (iaNaviguerSuggestions(e)) return;
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            iaEnvoyer();
        }
    };
    input.oninput = () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 150) + 'px';
        iaGererSaisieCommande();
    };
    input.onblur = () => setTimeout(iaMasquerSuggestions, 150);

    document.getElementById('ia-select-modele').onchange = async (e) => {
        if (iaConvCourante && e.target.value && e.target.value !== iaConvCourante.modele) {
            await iaFetchJSON(`/api/ia/conversations/${iaConvCourante.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ modele: e.target.value }),
            });
            iaConvCourante.modele = e.target.value;
            iaAjouterMarqueurModele(e.target.value);
        }
    };
}

function iaPanelVisible() {
    const panel = document.getElementById('panel-ia');
    return panel && panel.classList.contains('active');
}

function iaDemarrerPollingStatut() {
    if (iaStatutTimer) return;
    iaStatutTimer = setInterval(() => {
        if (iaPanelVisible()) iaMajStatut();
    }, 10000);
}

async function chargerIA() {
    iaBrancherUI();
    await iaMajStatut();
    await iaChargerModeles();
    await iaChargerArbo();
    await iaChargerCommandes();
    iaDemarrerPollingStatut();
}
