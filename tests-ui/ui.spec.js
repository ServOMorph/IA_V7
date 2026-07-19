const { test, expect } = require('@playwright/test');


test('parcours UI complet sur ordinateur', async ({ page, context }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop');
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', error => pageErrors.push(error.message));
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], {
    origin: 'http://127.0.0.1:4174'
  });

  await page.goto('/');
  await expect(page).toHaveTitle('IA V7 — SérénIA Tech');
  await expect(page.locator('.app-brand')).toHaveText('SérénIA Tech');
  await expect(page.locator('#ia-statut-serveur')).toHaveAttribute('title', 'Serveur Ollama actif');
  await expect(page.locator('#ia-modele-charge')).toContainText('gemma4:e4b');
  await expect(page.locator('#ia-select-modele option')).toHaveCount(2);

  const primaryColor = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim()
  );
  expect(primaryColor).toBe('rgb(165, 201, 202)');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(26, 32, 44)');
  await page.emulateMedia({ colorScheme: 'light' });
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(255, 255, 255)');

  page.once('dialog', dialog => dialog.accept('TEST_UI_AUTOMATISE'));
  await page.locator('#ia-btn-nouveau-dossier').click();
  let folder = page.locator('.ia-dossier').filter({ hasText: 'TEST_UI_AUTOMATISE' });
  await expect(folder).toHaveCount(1);

  const folderName = folder.locator('.ia-dossier-nom');
  await folderName.dblclick();
  const renameInput = page.locator('.ia-rename-input');
  await expect(renameInput).toHaveCount(1);
  await renameInput.fill('TEST_UI_AUTOMATISE_RENOMME');
  await renameInput.press('Enter');
  folder = page.locator('.ia-dossier').filter({ hasText: 'TEST_UI_AUTOMATISE_RENOMME' });
  await expect(folder).toHaveCount(1);

  await folder.locator('.ia-dossier-prompt').click();
  await folder.locator('.ia-prompt-input').fill('Réponds en français.');
  await folder.locator('.ia-prompt-save').click();
  await expect(folder.locator('.ia-prompt-save')).toHaveText('Enregistré ✓');

  await folder.locator('.ia-dossier-nouvelle-conv').click();
  await expect(page.locator('#ia-titre-conv')).toHaveText('Nouvelle conversation');
  await page.locator('#ia-input').fill('Réponds uniquement : TEST OK.');
  await page.locator('#ia-btn-envoyer').click();
  await expect(page.locator('.ia-bulle-user')).toContainText('TEST OK');
  await expect(page.locator('.ia-bulle-assistant')).toContainText('TEST OK');
  await expect(page.locator('#ia-btn-envoyer')).toBeVisible();
  await expect(page.locator('#ia-titre-conv')).toHaveText('Titre automatique test');

  folder = page.locator('.ia-dossier').filter({ hasText: 'TEST_UI_AUTOMATISE_RENOMME' });
  let conversation = folder.locator('.ia-conv').filter({ hasText: 'Titre automatique test' });
  await conversation.locator('.ia-conv-nom').dblclick();
  const conversationRename = page.locator('.ia-rename-input');
  await conversationRename.fill('Conversation UI automatisée');
  await conversationRename.press('Enter');
  await expect(page.locator('#ia-titre-conv')).toHaveText('Conversation UI automatisée');

  await page.locator('#ia-select-modele').selectOption('modele-test:latest');
  await expect(page.locator('.ia-marqueur-modele')).toHaveText('Modèle : modele-test:latest');
  await page.locator('#ia-btn-defaut').click();
  await expect(page.locator('#ia-btn-defaut')).toHaveText('Défaut ✓');
  await page.locator('#ia-btn-charger').click();
  await expect(page.locator('#ia-modele-charge')).toContainText('modele-test:latest');
  await page.locator('#ia-btn-decharger').click();
  await expect(page.locator('#ia-modele-charge')).toContainText('aucun modèle chargé');

  await page.locator('#ia-input').fill('MARKDOWN_TEST');
  await page.locator('#ia-btn-envoyer').click();
  await expect(page.locator('.ia-bulle-assistant h1')).toHaveText('Titre test');
  await expect(page.locator('.ia-bulle-assistant pre code')).toContainText("print('ok')");
  expect(await page.evaluate(() => window.__xss_test)).toBeUndefined();
  await expect(page.locator('.ia-bulle-assistant script')).toHaveCount(0);
  const markdownBubble = page.locator('.ia-bulle-assistant').filter({ hasText: 'Titre test' });
  await markdownBubble.locator('.ia-copier').click();
  await expect(markdownBubble.locator('.ia-copier')).toHaveText('Copié ✓');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain('# Titre test');

  await page.locator('#ia-input').fill('LIVRABLE_TEST');
  await page.locator('#ia-btn-envoyer').click();
  const deliverable = page.locator('.ia-livrable').last();
  await expect(deliverable).toContainText('Contenu livrable automatisé');
  await deliverable.locator('[data-action="copier"]').click();
  await expect(deliverable.locator('[data-action="copier"]')).toHaveText('Copié ✓');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    'Contenu livrable automatisé'
  );
  const downloadPromise = page.waitForEvent('download');
  await deliverable.locator('[data-action="telecharger"]').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('livrable.txt');

  await page.locator('#ia-input').fill('ligne un\nligne deux');
  await page.locator('#ia-input').press('Shift+Enter');
  await expect(page.locator('#ia-input')).toHaveValue('ligne un\nligne deux\n');
  await page.locator('#ia-input').fill('GENERATION_LONGUE_TEST');
  await page.locator('#ia-btn-envoyer').click();
  await expect(page.locator('#ia-btn-stop')).toBeVisible();
  await page.locator('#ia-btn-stop').click();
  await expect(page.locator('#ia-btn-envoyer')).toBeVisible();
  await expect(page.locator('#ia-input')).toBeEnabled();

  await page.locator('#ia-input').fill('/help');
  const assistantCountBeforeHelp = await page.locator('.ia-bulle-assistant').count();
  const userCountBeforeHelp = await page.locator('.ia-bulle-user').count();
  await expect(page.locator('#ia-modal-help')).toBeVisible();
  await expect(page.locator('#ia-modal-help-titre')).toHaveText('Commandes disponibles');
  await expect(page.locator('#ia-help-commandes')).toContainText('/help');
  await expect(page.locator('#ia-help-commandes')).toContainText('/write');
  await expect(page.locator('.ia-bulle-assistant')).toHaveCount(assistantCountBeforeHelp);
  await expect(page.locator('.ia-bulle-user')).toHaveCount(userCountBeforeHelp);
  await page.keyboard.press('Enter');
  await expect(page.locator('#ia-modal-help')).toBeHidden();
  await expect(page.locator('#ia-input')).toHaveValue('');

  await page.locator('#ia-input').fill('/write test_ui_write');
  await page.locator('#ia-btn-envoyer').click();
  const writeBubble = page.locator('.ia-bulle-assistant').last();
  await expect(writeBubble).toContainText('Fichier écrit');
  await expect(writeBubble).toHaveClass(/ia-bulle-commande/);

  await page.locator('#ia-input').fill('/rgpd Contact : jean.dupont@example.com au 06 12 34 56 78');
  await page.locator('#ia-btn-envoyer').click();
  const rgpdBubble = page.locator('.ia-bulle-assistant').last();
  await expect(rgpdBubble).toContainText('[DONNÉE_SENSIBLE]');
  await expect(rgpdBubble).not.toContainText('jean.dupont@example.com');
  await expect(rgpdBubble).toHaveClass(/ia-bulle-commande/);

  await page.locator('#ia-input').fill('/inconnue');
  await page.locator('#ia-btn-envoyer').click();
  const commandeErreurBubble = page.locator('.ia-bulle-assistant').last();
  await expect(commandeErreurBubble).toContainText('Commande inconnue');
  await expect(commandeErreurBubble).toHaveClass(/ia-bulle-commande-erreur/);

  await page.locator('#ia-btn-capture').click();
  await expect(page.locator('#ia-capture-overlay')).toBeVisible();
  await page.mouse.move(400, 300);
  await page.mouse.down();
  await page.mouse.move(700, 500);
  await page.mouse.up();
  await expect(page.locator('#ia-capture-rect')).toBeVisible();
  await expect(page.locator('#ia-capture-valider')).toBeVisible();
  await page.mouse.move(700, 500);
  await page.mouse.down();
  await page.mouse.move(760, 560);
  await page.mouse.up();
  const rectBox = await page.locator('#ia-capture-rect').boundingBox();
  expect(Math.round(rectBox.width)).toBeGreaterThan(350);
  const capturePromise = page.waitForResponse(r =>
    r.url().includes('/api/ia/captures') && r.request().method() === 'POST');
  await page.locator('#ia-capture-valider').click();
  const captureResponse = await capturePromise;
  expect(captureResponse.status()).toBe(201);
  const captureBody = await captureResponse.json();
  expect(captureBody.fichier).toMatch(/^capture_.*\.png$/);
  await expect(page.locator('.ia-capture-toast')).toContainText('Capture enregistrée');
  await expect(page.locator('#ia-capture-overlay')).toHaveCount(0);

  await page.locator('#ia-btn-capture').click();
  await page.keyboard.press('Escape');
  await expect(page.locator('#ia-capture-overlay')).toHaveCount(0);

  await page.locator('#ia-input').fill('ERREUR_RESEAU_TEST');
  await page.locator('#ia-input').press('Enter');
  await expect(page.locator('.ia-bulle-assistant').last()).toContainText(
    'Erreur : Erreur réseau simulée'
  );
  await expect(page.locator('#ia-btn-envoyer')).toBeVisible();

  await page.reload();
  folder = page.locator('.ia-dossier').filter({ hasText: 'TEST_UI_AUTOMATISE_RENOMME' });
  await folder.locator('.ia-dossier-toggle').click();
  conversation = folder.locator('.ia-conv').filter({ hasText: 'Conversation UI automatisée' });
  await conversation.locator('.ia-conv-nom').click();
  await expect(page.locator('.ia-bulle-user')).toHaveCount(8);
  expect(await page.locator('.ia-bulle-assistant').count()).toBeGreaterThanOrEqual(3);

  await page.locator('#ia-ephemere').check();
  await page.locator('#ia-btn-nouvelle-conv').click();
  await expect(page.locator('#ia-titre-conv')).toHaveText('Éphémère');
  await page.locator('#ia-input').fill('MESSAGE_EPHEMERE_TEST');
  await page.locator('#ia-btn-envoyer').click();
  await expect(page.locator('.ia-bulle-assistant')).toContainText('TEST OK');
  await page.reload();
  await expect(page.locator('.ia-conv-nom', { hasText: 'Éphémère' })).toHaveCount(0);

  await page.locator('#ia-btn-serveur').click();
  await expect(page.locator('#ia-statut-serveur')).toHaveAttribute('title', 'Serveur Ollama arrêté');
  await expect(page.locator('#ia-btn-serveur')).toHaveText('Démarrer serveur');
  await page.locator('#ia-btn-serveur').click();
  await expect(page.locator('#ia-statut-serveur')).toHaveAttribute('title', 'Serveur Ollama actif');

  folder = page.locator('.ia-dossier').filter({ hasText: 'TEST_UI_AUTOMATISE_RENOMME' });
  await folder.locator('.ia-dossier-toggle').click();
  conversation = folder.locator('.ia-conv').filter({ hasText: 'Conversation UI automatisée' });
  await expect(conversation).toHaveCount(1);
  await expect(conversation).toBeVisible();
  page.once('dialog', dialog => dialog.dismiss());
  await conversation.locator('.ia-conv-suppr').click();
  await expect(conversation).toHaveCount(1);
  page.once('dialog', dialog => dialog.accept());
  await conversation.locator('.ia-conv-suppr').click();
  await expect(folder.locator('.ia-conv')).toHaveCount(0);

  page.once('dialog', dialog => dialog.dismiss());
  await folder.locator('.ia-dossier-suppr').click();
  await expect(folder).toHaveCount(1);
  page.once('dialog', dialog => dialog.accept());
  await folder.locator('.ia-dossier-suppr').click();
  await expect(folder).toHaveCount(0);

  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter(message => !message.includes('503'))).toEqual([]);
});


test('mise en page mobile', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile');
  await page.goto('/');
  await expect(page.locator('.app-brand')).toBeVisible();
  await expect(page.locator('.ia-sidebar')).toBeVisible();
  await expect(page.locator('.ia-chat')).toBeVisible();

  const metrics = await page.evaluate(() => {
    const sidebar = document.querySelector('.ia-sidebar').getBoundingClientRect();
    const chat = document.querySelector('.ia-chat').getBoundingClientRect();
    return {
      viewportWidth: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      sidebarTop: sidebar.top,
      chatTop: chat.top,
      inputRight: document.querySelector('#ia-input').getBoundingClientRect().right
    };
  });
  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.viewportWidth);
  expect(metrics.chatTop).toBeGreaterThan(metrics.sidebarTop);
  expect(metrics.inputRight).toBeLessThanOrEqual(metrics.viewportWidth);
  await expect(page.locator('#ia-btn-envoyer')).toBeVisible();

  for (const size of [
    { width: 768, height: 900 },
    { width: 1024, height: 900 },
    { width: 1440, height: 1000 }
  ]) {
    await page.setViewportSize(size);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - window.innerWidth
    );
    expect(overflow).toBeLessThanOrEqual(0);
  }
});
