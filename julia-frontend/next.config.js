/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['images.unsplash.com', 'via.placeholder.com'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  async rewrites() {
    return [
      {
        source: '/api/agents/:path*',
        destination: 'http://127.0.0.1:8000/api/agents/:path*',
      },
      {
        source: '/api/students/:path*',
        destination: 'http://127.0.0.1:8000/api/students/:path*',
      },
      {
        source: '/api/system/:path*',
        destination: 'http://127.0.0.1:8000/api/system/:path*',
      },
    ]
  },
}

module.exports = nextConfig
