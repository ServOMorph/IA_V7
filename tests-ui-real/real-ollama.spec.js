const { test, expect } = require('@playwright/test');


test('échange UI réel avec gemma4:e4b', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  await page.goto('/');
  await expect(page.locator('#ia-statut-serveur')).toHaveAttribute(
    'title',
    'Serveur Ollama actif'
  );
  await expect(page.locator('#ia-modele-charge')).toContainText('gemma4:e4b');
  await page.locator('#ia-select-modele').selectOption('gemma4:e4b');
  await page.locator('#ia-ephemere').check();
  await page.locator('#ia-btn-nouvelle-conv').click();
  await expect(page.locator('#ia-titre-conv')).toHaveText('Éphémère');

  await page.locator('#ia-input').fill('Réponds uniquement : OK.');
  await page.locator('#ia-btn-envoyer').click();
  const answer = page.locator('.ia-bulle-assistant .ia-bulle-corps');
  await expect(answer).toContainText('OK');
  await expect(page.locator('#ia-btn-envoyer')).toBeVisible();
  await expect(page.locator('#ia-input')).toBeEnabled();
  expect(pageErrors).toEqual([]);
});

