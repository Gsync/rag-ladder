import { cp, mkdir } from 'node:fs/promises';
import { basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = fileURLToPath(new URL('../../datasets/npm', import.meta.url));
const dest = fileURLToPath(new URL('../static/data/npm', import.meta.url));

const EXCLUDED_DIRS = new Set(['raw', 'readmes']);

await mkdir(dest, { recursive: true });
await cp(src, dest, {
	recursive: true,
	filter: (path) => !EXCLUDED_DIRS.has(basename(path))
});

console.log(`Copied datasets/npm -> ${dest}`);
