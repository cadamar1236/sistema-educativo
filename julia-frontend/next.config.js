/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: ['images.unsplash.com', 'via.placeholder.com'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  async rewrites() {
    return [
      {
        source: '/api/agents/:path*',
        destination: '/api/agents/:path*',
      },
      {
        source: '/api/students/:path*',
        destination: '/api/students/:path*',
      },
      {
        source: '/api/system/:path*',
        destination: '/api/system/:path*',
      },
    ]
  },
}

module.exports = nextConfig
