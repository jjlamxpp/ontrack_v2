export const config = {
  API_URL: import.meta.env.VITE_API_URL || 'https://ontrack-d4m7j.ondigitalocean.app/api',
  ENV: import.meta.env.VITE_ENV || 'production'
};

// Log the configuration
console.log('Config initialized:', config);
