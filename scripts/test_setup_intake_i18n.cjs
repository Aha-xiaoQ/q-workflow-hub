/* Run with Node + Playwright. Set PLAYWRIGHT_BROWSER_EXECUTABLE if needed.
 * Optional first argument: a private output folder for screenshots.
 * API calls are mocked: this test never installs a workflow or opens a picker.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const output = process.argv[2] && path.resolve(process.argv[2]);
const errors = [];
let runner = false;
let installResult = { ok: true, output: 'Test runner output.' };
let capturedPayload;
let capturedFolderTitle;

(async () => {
  if (output) await fs.mkdir(output, { recursive: true });
  const server = http.createServer(async (req, res) => {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    const file = pathname === '/assets/q-logo.svg' ? 'assets/q-logo.svg' : 'setup-intake.html';
    res.setHeader('Content-Type', file.endsWith('.svg') ? 'image/svg+xml' : 'text/html; charset=utf-8');
    res.end(await fs.readFile(path.join(root, file)));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_BROWSER_EXECUTABLE || undefined });
    const context = await browser.newContext();
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const pathname = new URL(route.request().url()).pathname;
      let result = { ok: true, mode: runner ? 'runner' : 'static' };
      if (pathname === '/api/choose-folder') {
        capturedFolderTitle = route.request().postDataJSON().title;
        result = { ok: true, path: 'C:\\Chosen' };
      }
      if (pathname === '/api/install') {
        capturedPayload = route.request().postDataJSON();
        result = installResult;
      }
      await route.fulfill({ status: result.ok ? 200 : 500, json: result });
    });
    const address = `http://127.0.0.1:${server.address().port}/setup-intake.html`;
    async function load(locale = 'en', hash = '') {
      await page.goto('about:blank');
      await page.goto(`${address}?lang=${locale}${hash}`);
      await page.waitForFunction(() => document.getElementById('modeBadge').textContent !== '检测安装模式');
      await page.waitForLoadState('networkidle');
    }
    async function toggle(locale) {
      await page.locator(`[data-ui-language="${locale}"]`).click();
      assert.equal(await page.locator('html').getAttribute('lang'), locale === 'zh' ? 'zh-CN' : 'en');
    }
    async function assertEnglish() {
      const text = (await page.locator('body').innerText()).replaceAll('中文', '');
      assert(!/[\u3400-\u9fff]/.test(text), `Untranslated visible text: ${text}`);
    }
    async function assertNoOverflow() {
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Page overflows horizontally');
    }

    for (const locale of ['en', 'zh-CN']) {
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 });
        await load(locale);
        assert.equal(await page.locator('html').getAttribute('lang'), locale);
        assert.equal(await page.locator('#language').inputValue(), locale === 'en' ? 'en' : 'zh');
        for (let step = 0; step < 4; step++) {
          await page.locator(`[data-step="${step}"]`).click();
          await assertNoOverflow();
          if (locale === 'en') await assertEnglish();
          if (output && [0, 3].includes(step)) {
            await page.screenshot({ path: path.join(output, `${locale}-${width}-step${step}.png`), fullPage: true });
          }
        }
        assert((await page.locator('#promptOut').innerText()).includes(locale === 'en' ? 'MACHINE_BOOTSTRAP.md' : 'MACHINE_BOOTSTRAP.zh-CN.md'));
      }
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await load();
    await toggle('zh');
    assert.equal(await page.locator('#userName').inputValue(), '小Q');
    assert((await page.locator('#preferences').inputValue()).startsWith('请用中文'));
    await toggle('en');
    assert.equal(await page.locator('#userName').inputValue(), 'Xiao Q');
    assert((await page.locator('#preferences').inputValue()).startsWith('Please'));
    await page.locator('#userName').fill('Alex <&>');
    await page.locator('#workflowLabel').fill('My Flow');
    await page.locator('#agent').selectOption({ index: 2 });
    await page.locator('[data-step="1"]').click();
    await page.locator('#workspaceRoot').fill('C:\\UserWorkspace');
    assert.equal(await page.locator('#workflowHubPath').inputValue(), 'C:\\UserWorkspace\\workflow-hub');
    await page.locator('#workflowHubPath').fill('D:\\PrivateCustom');
    await page.locator('#workspaceRoot').fill('C:\\ChangedWorkspace');
    assert.equal(await page.locator('#workflowHubPath').inputValue(), 'D:\\PrivateCustom');
    await page.locator('#codexHome').fill('D:\\TestCodex');
    await page.locator('#workflowHubRemote').fill('https://example.invalid/private.git');
    await page.locator('[data-step="2"]').click();
    await page.locator('#preferences').fill('Keep my custom notes.');
    await page.locator('#initializeGit').uncheck();
    const values = () => page.locator('input[id], textarea, select').evaluateAll(elements => elements.map(element => [element.id, element.value, element.checked]));
    const before = await values();
    await toggle('zh');
    await toggle('en');
    assert.deepEqual(await values(), before, 'Language switching changed custom field values');
    assert((await page.locator('#promptOut').innerText()).includes('Alex <&>'));
    assert((await page.locator('#promptOut').innerText()).includes('Keep my custom notes.'));
    await page.locator('[data-step="0"]').click();
    await page.locator('#language').selectOption('zh');
    assert.equal(await page.locator('html').getAttribute('lang'), 'zh-CN');
    assert((await page.locator('#promptOut').innerText()).startsWith('请从'));
    await page.locator('#userName').fill('');
    await page.locator('#workflowLabel').fill('');
    await page.locator('[data-step="3"]').click();
    assert((await page.locator('#warningBox').innerText()).includes('为空'));
    await toggle('en');
    assert((await page.locator('#warningBox').innerText()).includes('Enter a resume phrase'));

    await load('en', '#review');
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.copiedText = text; } } }));
    await page.locator('#nextStep').click();
    assert.equal(await page.evaluate(() => window.copiedText), await page.locator('#promptOut').innerText());
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw new Error('clipboard denied'); } } }));
    await page.locator('#nextStep').click();
    assert((await page.locator('#statusText').innerText()).includes('copy it manually'));
    assert((await page.evaluate(() => getSelection().toString())).startsWith('Set up q-workflow'));

    for (const locale of ['en', 'zh-CN']) {
      const localUrl = pathToFileURL(path.join(root, 'setup-intake.html'));
      localUrl.searchParams.set('lang', locale);
      localUrl.hash = 'paths';
      await page.goto(localUrl.href);
      await page.waitForFunction(() => document.getElementById('modeBadge').textContent !== '检测安装模式');
      assert.equal(await page.locator('html').getAttribute('lang'), locale);
      await page.evaluate(() => Object.defineProperty(window, 'showDirectoryPicker', { configurable: true, value: undefined }));
      const dialogPromise = page.waitForEvent('dialog');
      const clickPromise = page.locator('[data-path-target="workspaceRoot"]').click();
      const dialog = await dialogPromise;
      assert(dialog.message().includes(locale === 'en' ? 'Paste the full folder path' : '请粘贴文件夹完整路径'));
      await dialog.accept('C:\\ManualFolder');
      await clickPromise;
      assert.equal(await page.locator('#workspaceRoot').inputValue(), 'C:\\ManualFolder');
    }

    runner = true;
    for (const locale of ['en', 'zh-CN']) {
      await load(locale, '#paths');
      await page.locator('[data-path-target="workspaceRoot"]').click();
      await page.waitForFunction(() => document.getElementById('workspaceRoot').value === 'C:\\Chosen');
      assert.equal(capturedFolderTitle, locale === 'en' ? 'Choose a folder' : '请选择文件夹');
      assert.equal(await page.locator('#workspaceRoot').inputValue(), 'C:\\Chosen');
      await page.locator('[data-step="3"]').click();
      installResult = { ok: false, error: 'Simulated failure' };
      await page.locator('#nextStep').click();
      await page.waitForFunction(() => !document.getElementById('nextStep').disabled);
      assert((await page.locator('#statusText').innerText()).includes(locale === 'en' ? 'Installation failed' : '安装失败'));
      installResult = { ok: true, output: 'Test runner output.' };
      await page.locator('#nextStep').click();
      await page.waitForFunction(() => !document.getElementById('nextStep').disabled);
      assert.equal(capturedPayload.language, locale === 'en' ? 'en' : 'zh');
      assert.equal(capturedPayload.workspaceRoot, 'C:\\Chosen');
      assert((await page.locator('#installLog').innerText()).includes(locale === 'en' ? 'Next steps:' : '下一步：'));
      await toggle(locale === 'en' ? 'zh' : 'en');
      assert((await page.locator('#installLog').innerText()).includes(locale === 'en' ? '下一步：' : 'Next steps:'));
      assert((await page.locator('#installLog').innerText()).includes('Test runner output.'));
    }
    assert.deepEqual(errors, [], 'Browser script errors');
    console.log('PASS: two locales, 1440/390px, four steps, query/hash routing, direct file mode, defaults/custom values, folder sync/manual fallback, warnings, clipboard/fallback, and mocked runner success/failure.');
    if (output) console.log(`Screenshots: ${output}`);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
