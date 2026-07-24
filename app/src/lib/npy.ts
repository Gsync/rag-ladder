const MAGIC = [0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59]; // \x93NUMPY

export function loadNpy(buffer: ArrayBuffer): { data: Float32Array; shape: number[] } {
	const view = new DataView(buffer);

	for (let i = 0; i < MAGIC.length; i++) {
		if (view.getUint8(i) !== MAGIC[i]) {
			throw new Error('not a valid .npy file (bad magic string)');
		}
	}

	const majorVersion = view.getUint8(6);

	let headerLen: number;
	let headerStart: number;
	if (majorVersion === 1) {
		headerLen = view.getUint16(8, true);
		headerStart = 10;
	} else {
		headerLen = view.getUint32(8, true);
		headerStart = 12;
	}

	const headerBytes = new Uint8Array(buffer, headerStart, headerLen);
	const header = new TextDecoder('ascii').decode(headerBytes);

	const descrMatch = header.match(/'descr':\s*'([^']*)'/);
	const fortranMatch = header.match(/'fortran_order':\s*(True|False)/);
	const shapeMatch = header.match(/'shape':\s*\(([^)]*)\)/);

	if (!descrMatch || descrMatch[1] !== '<f4') {
		throw new Error(`unsupported .npy dtype: ${descrMatch?.[1] ?? 'unknown'} (expected <f4)`);
	}
	if (!fortranMatch || fortranMatch[1] !== 'False') {
		throw new Error('unsupported .npy layout: expected fortran_order=False (C order)');
	}
	if (!shapeMatch) {
		throw new Error('could not parse .npy shape from header');
	}

	const shape = shapeMatch[1]
		.split(',')
		.map((s) => s.trim())
		.filter((s) => s.length > 0)
		.map((s) => parseInt(s, 10));

	const dataStart = headerStart + headerLen;
	const totalElements = shape.reduce((a, b) => a * b, 1);

	return { data: new Float32Array(buffer, dataStart, totalElements), shape };
}
