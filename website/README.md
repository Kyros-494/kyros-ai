# Kyros Website

> **Official marketing and documentation website for Kyros**

Modern, responsive Next.js website built with React 19, TypeScript, and Tailwind CSS 4.

---

## 🚀 Quick Start

### Prerequisites

- **Node.js**: 20+ (LTS recommended)
- **npm**: 10+ (comes with Node.js)

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start

# Or export static site
npm run build && npm run export
```

---

## 📁 Project Structure

```
website/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout with metadata
│   │   ├── page.tsx            # Landing page
│   │   ├── globals.css         # Global styles + Tailwind
│   │   ├── sitemap.ts          # Auto-generated sitemap
│   │   └── favicon.ico         # Favicon
│   └── components/             # React components (future)
├── public/                     # Static assets
│   ├── kyros-logo.png          # Logo
│   ├── og-image.png            # Open Graph image
│   ├── apple-touch-icon.png    # iOS icon
│   ├── robots.txt              # SEO robots file
│   └── favicon.ico             # Favicon
├── .env.example                # Environment variables template
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration (optional)
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies and scripts
└── README.md                   # This file
```

---

## 🎨 Tech Stack

### Core

- **[Next.js 16](https://nextjs.org/)** - React framework with App Router
- **[React 19](https://react.dev/)** - UI library
- **[TypeScript 5](https://www.typescriptlang.org/)** - Type safety
- **[Tailwind CSS 4](https://tailwindcss.com/)** - Utility-first CSS (beta)

### Features

- ✅ Server-side rendering (SSR)
- ✅ Static site generation (SSG)
- ✅ Responsive design (mobile-first)
- ✅ Dark mode support
- ✅ SEO optimization
- ✅ Security headers
- ✅ Image optimization
- ✅ Font optimization (Geist Sans + Mono)

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
```

**Required Variables**:
```env
NEXT_PUBLIC_SITE_URL=https://kyros.ai
NEXT_PUBLIC_API_URL=https://api.kyros.ai
```

**Optional Variables**:
```env
# Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=kyros.ai

# Error Tracking
NEXT_PUBLIC_SENTRY_DSN=https://...

# Feature Flags
NEXT_PUBLIC_ENABLE_DOCS=true
```

### Next.js Configuration

Edit `next.config.ts` to customize:
- Security headers
- Redirects and rewrites
- Image domains
- Compression settings

### Tailwind CSS

Tailwind CSS 4 uses CSS-based configuration in `src/app/globals.css`:

```css
@theme {
  --color-primary: #3b82f6;
  --font-sans: 'Geist Sans', sans-serif;
}
```

For Tailwind 3 compatibility, create `tailwind.config.ts`.

---

## 🎯 Features

### Landing Page

- **Hero Section**: Compelling headline with gradient text
- **Stats Section**: Key metrics (4 stats)
- **Features Grid**: 6 feature cards with icons
- **Quickstart**: 3-step installation guide with code
- **Integrations**: 8 framework badges
- **Navigation**: Sticky header with links
- **Footer**: Copyright and links

### SEO

- ✅ Meta tags (title, description, keywords)
- ✅ Open Graph tags (Facebook, LinkedIn)
- ✅ Twitter Card tags
- ✅ Canonical URLs
- ✅ Sitemap (auto-generated)
- ✅ Robots.txt
- ✅ Structured data (future)

### Security

- ✅ Security headers configured
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection enabled
- ✅ Referrer-Policy configured
- ✅ Permissions-Policy configured
- ✅ Powered-by header disabled

### Performance

- ✅ Static generation (SSG)
- ✅ Image optimization (next/image)
- ✅ Font optimization (next/font)
- ✅ Compression enabled
- ✅ Minimal JavaScript
- ✅ Tree-shakeable CSS

---

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

**Or connect GitHub repo** for automatic deployments.

### Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy

# Production deployment
netlify deploy --prod
```

### Docker

```bash
# Build image
docker build -t kyros-website .

# Run container
docker run -p 3000:3000 kyros-website
```

### Static Export

```bash
# Build and export
npm run build
npm run export

# Deploy /out directory to any static host
```

---

## 🧪 Development

### Scripts

```bash
# Development server (hot reload)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

### Code Quality

```bash
# ESLint
npm run lint

# Fix linting issues
npm run lint -- --fix

# Type checking
npx tsc --noEmit
```

### Adding Pages

Create new pages in `src/app/`:

```typescript
// src/app/about/page.tsx
export default function AboutPage() {
  return <div>About Kyros</div>;
}
```

### Adding Components

Create reusable components in `src/components/`:

```typescript
// src/components/Button.tsx
export function Button({ children }: { children: React.ReactNode }) {
  return <button className="...">{children}</button>;
}
```

---

## 📊 Performance

### Lighthouse Scores (Target)

- **Performance**: 95+
- **Accessibility**: 100
- **Best Practices**: 100
- **SEO**: 100

### Optimization Tips

1. **Images**: Use `next/image` for automatic optimization
2. **Fonts**: Use `next/font` for font optimization
3. **Code Splitting**: Automatic with Next.js App Router
4. **Lazy Loading**: Use `dynamic()` for heavy components
5. **Caching**: Configure cache headers in `next.config.ts`

---

## 🎨 Styling

### Tailwind CSS

Use utility classes for styling:

```tsx
<div className="flex items-center justify-center p-4 bg-gray-100 dark:bg-gray-900">
  <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
    Hello World
  </h1>
</div>
```

### Dark Mode

Dark mode is automatic based on system preference:

```tsx
<div className="bg-white dark:bg-black">
  <p className="text-black dark:text-white">Content</p>
</div>
```

### Custom Styles

Add custom CSS in `src/app/globals.css`:

```css
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600;
  }
}
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
npx kill-port 3000

# Or use different port
PORT=3001 npm run dev
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules
rm -rf node_modules package-lock.json
npm install
```

### Type Errors

```bash
# Check TypeScript errors
npx tsc --noEmit

# Update TypeScript
npm install -D typescript@latest
```

---

## 📚 Resources

### Documentation

- **Next.js**: https://nextjs.org/docs
- **React**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs

### Kyros Resources

- **Homepage**: https://kyros.ai
- **Documentation**: https://docs.kyros.ai
- **GitHub**: https://github.com/Kyros-494/kyros-ai
- **API Docs**: https://api.kyros.ai/docs

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test locally: `npm run dev`
5. Build: `npm run build`
6. Commit: `git commit -m "feat: add new feature"`
7. Push and create a pull request

---

## 📄 License

The Kyros website is part of the Kyros project and is licensed under the **Apache License 2.0**. See [LICENSE](../LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [Next.js](https://nextjs.org/) - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [Vercel](https://vercel.com/) - Deployment platform
- [Geist Font](https://vercel.com/font) - Typography

---

**Made with ❤️ by the Kyros team**
