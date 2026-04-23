export const PIPELINE_STAGES = ['Uploading', 'OCR', 'Extraction', 'Validation', 'Completed'] as const;
export type Stage = (typeof PIPELINE_STAGES)[number];
