/** Kyros SDK error classes. */

export class KyrosError extends Error {
  public readonly statusCode: number | undefined;
  public readonly errorCode: string | undefined;

  constructor(message: string, statusCode?: number, errorCode?: string) {
    super(message);
    this.name = 'KyrosError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
  }
}

export class AuthenticationError extends KyrosError {
  constructor(message = 'Authentication failed', statusCode = 401, errorCode?: string) {
    super(message, statusCode, errorCode);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends KyrosError {
  public readonly limit: number;
  public readonly remaining: number;
  public readonly resetAt: number;
  public readonly retryAfter: number;

  constructor(
    message = 'Rate limit exceeded',
    limit = 0,
    remaining = 0,
    resetAt = 0,
    errorCode?: string,
  ) {
    super(message, 429, errorCode);
    this.name = 'RateLimitError';
    this.limit = limit;
    this.remaining = remaining;
    this.resetAt = resetAt;
    this.retryAfter = Math.max(0, resetAt - Math.floor(Date.now() / 1000));
  }
}

export class NotFoundError extends KyrosError {
  constructor(message = 'Resource not found', errorCode?: string) {
    super(message, 404, errorCode);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends KyrosError {
  constructor(message = 'Validation error', errorCode?: string) {
    super(message, 422, errorCode);
    this.name = 'ValidationError';
  }
}

export class ServerError extends KyrosError {
  constructor(message = 'Internal server error', statusCode = 500, errorCode?: string) {
    super(message, statusCode, errorCode);
    this.name = 'ServerError';
  }
}
