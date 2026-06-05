import type { NextConfig } from 'next';

const isGithubActions = process.env.GITHUB_ACTIONS === 'true';

const nextConfig: NextConfig = {
  // Catch potential issues during development
  reactStrictMode: true,

  // Don't expose the framework in response headers
  poweredByHeader: false,

  // Compress responses
  compress: true,

  // Enable static export for GitHub Pages, standalone for Docker otherwise
  output: isGithubActions ? 'export' : 'standalone',

  // Set base path only for GitHub Pages
  basePath: isGithubActions ? '/kyros-ai' : '',

  // Disable image optimization for static export
  images: {
    unoptimized: isGithubActions ? true : false,
  },

  // Security headers applied to all routes (disabled in static export mode)
  ...(isGithubActions ? {} : {
    async headers() {
      return [
        {
          source: '/(.*)',
          headers: [
            { key: 'X-Content-Type-Options', value: 'nosniff' },
            { key: 'X-Frame-Options', value: 'DENY' },
            { key: 'X-XSS-Protection', value: '1; mode=block' },
            { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
            {
              key: 'Permissions-Policy',
              value: 'camera=(), microphone=(), geolocation=()',
            },
          ],
        },
      ];
    },
  }),
};

export default nextConfig;
