/**
 * Custom logger utility to control console.error output
 * Set ENABLE_ERROR_LOGS=false in .env to disable all console.error logs
 */

// Patterns to filter out (errors that should not be logged)
const FILTERED_ERROR_PATTERNS = [
  'SIGN_IN_CANCELLED',
  'cancelled',
  'canceled',
  'popup-closed-by-user',
  'cancelled-popup-request',
  'permission-denied',
  'Missing or insufficient permissions',
  'Uncaught Error in snapshot listener',
  '@firebase/firestore',
];

// Original console methods
const originalError = console.error;
const originalWarn = console.warn;
const originalLog = console.log;

// Check if error logging is enabled (default: true)
const isErrorLoggingEnabled = () => {
  // Allow disabling via environment variable
  const envSetting = process.env.EXPO_PUBLIC_ENABLE_ERROR_LOGS;
  if (envSetting === 'false') {
    return false;
  }
  return true;
};

// Check if error should be filtered
const shouldFilterError = (message: any): boolean => {
  if (!isErrorLoggingEnabled()) {
    return true; // Filter all if logging is disabled
  }

  // Convert message to string for pattern matching
  let messageStr = '';
  
  if (typeof message === 'string') {
    messageStr = message;
  } else if (message instanceof Error) {
    messageStr = `${message.message} ${message.stack || ''}`;
  } else if (typeof message === 'object' && message !== null) {
    // Try to extract meaningful string from object
    messageStr = message.message || message.error || JSON.stringify(message);
  } else {
    messageStr = String(message);
  }

  // Check if message matches any filtered pattern
  return FILTERED_ERROR_PATTERNS.some(pattern => 
    messageStr.toLowerCase().includes(pattern.toLowerCase())
  );
};

/**
 * Override console.error to filter messages
 */
export const setupErrorFilter = () => {
  console.error = (...args: any[]) => {
    // Check if any argument matches filtered patterns
    const shouldFilter = args.some(arg => shouldFilterError(arg));
    
    if (!shouldFilter) {
      // Only log if not filtered
      originalError.apply(console, args);
    }
    // Otherwise, silently ignore (don't log filtered errors)
  };
};

/**
 * Override console.warn to filter messages (optional)
 */
export const setupWarnFilter = () => {
  console.warn = (...args: any[]) => {
    const shouldFilter = args.some(arg => shouldFilterError(arg));
    
    if (!shouldFilter) {
      originalWarn.apply(console, args);
    }
  };
};

/**
 * Restore original console methods
 */
export const restoreConsole = () => {
  console.error = originalError;
  console.warn = originalWarn;
  console.log = originalLog;
};

/**
 * Custom logger that respects filtering
 */
export const logger = {
  error: (...args: any[]) => {
    if (!shouldFilterError(args)) {
      originalError.apply(console, args);
    }
  },
  warn: (...args: any[]) => {
    originalWarn.apply(console, args);
  },
  log: (...args: any[]) => {
    originalLog.apply(console, args);
  },
  info: (...args: any[]) => {
    originalLog.apply(console, args);
  },
};

