// Run from ego-browser nodejs with the existing TaskSpace. This module never opens another browser.
import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const output = fileURLToPath(new URL('./retrieval/', import.meta.url));

export async function collect(task, batch) {
  await mkdir(output, { recursive: true });
  const results = await Promise.allSettled(batch.map(async (entry, index) => {
    const page = task.page(`p${index + 1}`);
    await page.goto(entry.url);
    const data = await page.evaluate(() => {
      const body = document.querySelector('#rso') || document.querySelector('main') || document.querySelector('[role="main"]') || document.querySelector('article') || document.body;
      const search = location.hostname.includes('google.');
      return {
        url: location.href,
        title: document.title,
        text: body.innerText,
        dates: [...document.querySelectorAll('time, meta[property*="published"], meta[property*="modified"], meta[name="date"], meta[name="citation_date"], meta[name="ms.date"], meta[name="updated_at"]')].map(n => n.getAttribute('datetime') || n.getAttribute('content') || n.textContent),
        links: [...document.querySelectorAll('a[href]')].filter(a => !search || a.querySelector('h3')).map(a => ({ title: a.innerText.trim(), url: a.href })).filter(a => a.title && /^https?:/.test(a.url)),
      };
    });
    const record = { id: entry.id, requested_url: entry.url, accessed_at: new Date().toISOString(), ...data, text_sha256: createHash('sha256').update(data.text).digest('hex') };
    await writeFile(output + entry.id + '.json', JSON.stringify(record, null, 2) + '\n');
    return { ...record, text: record.text.slice(0, entry.preview ?? 10000), links: record.links.filter(a => !a.url.includes('google.com')).slice(0, entry.linkLimit ?? 15) };
  }));
  results.forEach((result, index) => console.log(JSON.stringify({ id: batch[index].id, ...result, ...(result.status === 'rejected' ? { error: String(result.reason) } : {}) })));
}
