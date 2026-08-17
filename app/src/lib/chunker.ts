export type Chunk = { start: number; end: number; text: string };

export function chunkText(text: string, size: number, overlap: number): Chunk[] {
	const step = Math.max(1, size - overlap);
	const chunks: Chunk[] = [];
	for (let start = 0; start < text.length; start += step) {
		const end = Math.min(start + size, text.length);
		chunks.push({ start, end, text: text.slice(start, end) });
		if (end === text.length) break;
	}
	return chunks;
}
