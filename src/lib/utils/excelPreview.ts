export const MAX_EXCEL_PREVIEW_BYTES = 10 * 1024 * 1024;
export const MAX_EXCEL_PREVIEW_ROWS = 1000;
export const MAX_EXCEL_PREVIEW_COLS = 80;

export const assertExcelPreviewSize = (byteLength: number) => {
	if (byteLength > MAX_EXCEL_PREVIEW_BYTES) {
		throw new Error('Excel file is too large to preview safely. Please download it instead.');
	}
};

export const readExcelWorkbook = async (arrayBuffer: ArrayBuffer) => {
	assertExcelPreviewSize(arrayBuffer.byteLength);

	const XLSX = await import('xlsx');
	return XLSX.read(arrayBuffer, {
		type: 'array',
		dense: true,
		cellFormula: false,
		cellHTML: false,
		cellNF: false,
		cellStyles: false,
		bookDeps: false,
		bookVBA: false
	});
};
