import { pipeline, type FeatureExtractionPipeline } from '@huggingface/transformers';

// Must match the factory's model exactly (fastembed all-MiniLM-L6-v2, 384-dim) or
// neighbors are meaningless — see CLAUDE.md's embedding-model-mismatch warning.
const MODEL_ID = 'onnx-community/all-MiniLM-L6-v2-ONNX';

let extractorPromise: Promise<FeatureExtractionPipeline> | null = null;

function getExtractor(): Promise<FeatureExtractionPipeline> {
	if (!extractorPromise) {
		extractorPromise = pipeline('feature-extraction', MODEL_ID);
	}
	return extractorPromise;
}

export async function embed(text: string): Promise<Float32Array> {
	const extractor = await getExtractor();
	const output = await extractor(text, { pooling: 'mean', normalize: true });
	return output.data as Float32Array;
}
