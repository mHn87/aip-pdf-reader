/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Increase body size limit for large PDF uploads (200MB)
  serverRuntimeConfig: {
    maxFileSize: 200 * 1024 * 1024,
  },
  api: {
    bodyParser: {
      sizeLimit: '200mb',
    },
  },
}

module.exports = nextConfig
