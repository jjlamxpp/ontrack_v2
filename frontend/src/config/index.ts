export const config = {
  // Use a relative URL to avoid path issues with proxies
  API_URL: '',
  ENV: import.meta.env.VITE_ENV || 'production'
};

// Log the configuration
console.log('Config initialized:', config);
