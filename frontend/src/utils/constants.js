export const ALLOWED_FILE_EXTENSIONS = ['pdf', 'docx', 'txt', 'md'];

export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

export const DOCUMENT_STATUS = {
  UPLOADED: 'UPLOADED',
  PROCESSING: 'PROCESSING',
  PROCESSED: 'PROCESSED',
  FAILED: 'FAILED',
  CHUNKED: 'CHUNKED',
  EMBEDDED: 'EMBEDDED',
};

export const ERROR_MESSAGES = {
  UNAUTHORIZED: 'Your session has expired. Please sign in again.',
  FORBIDDEN: 'You do not have permission to access this workspace.',
  NOT_FOUND: 'The requested document could not be found.',
  PAYLOAD_TOO_LARGE: 'File exceeds the maximum allowed size of 25 MB.',
  SERVER_ERROR: 'The server encountered an error processing your request. Please try again later.',
  INVALID_FILE_TYPE: 'Only PDF, DOCX, TXT, and MD files are supported.',
  DUPLICATE_FILE: 'A document with identical content already exists in this workspace.',
  NETWORK_ERROR: 'Network connection error. Please check your network and try again.',
  GENERIC: 'An error occurred while processing the document.',
};
