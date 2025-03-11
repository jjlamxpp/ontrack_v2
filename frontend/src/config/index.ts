export const config = {
  // Use environment variable with fallback to relative URL
  API_URL: import.meta.env.VITE_API_URL || '/api',
  ENV: import.meta.env.VITE_ENV || 'production'
};

// Log the configuration
console.log('Config initialized:', config);
