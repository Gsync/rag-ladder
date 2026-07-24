export function cosineSimilarity(a: ArrayLike<number>, b: ArrayLike<number>): number {
	if (a.length !== b.length) {
		throw new Error(`vector length mismatch: ${a.length} vs ${b.length}`);
	}

	let dot = 0;
	let normA = 0;
	let normB = 0;
	for (let i = 0; i < a.length; i++) {
		dot += a[i] * b[i];
		normA += a[i] * a[i];
		normB += b[i] * b[i];
	}

	const denom = Math.sqrt(normA) * Math.sqrt(normB);
	return denom === 0 ? 0 : dot / denom;
}
