# Stud Frontend

This is the Next.js frontend application for Stud.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit: **http://localhost:3000**

## 📁 Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Homepage
│   ├── demo/              # Demo page
│   ├── mediquest/         # Game mode
│   ├── study/             # Document chat mode
│   ├── quiz/              # Quiz mode
│   ├── about/             # About page
│   ├── how-to-use/        # Usage guide
│   ├── auth/              # Login/Register
│   ├── components/        # React components
│   └── globals.css        # Global styles
├── lib/                   # Shared utilities
├── package.json          # Dependencies
├── next.config.mjs       # Next.js config
├── tailwind.config.js     # Tailwind config
└── tsconfig.json         # TypeScript config
```

## 🛠️ Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Environment Variables

Create `.env.local` in this directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 📝 Notes

- All frontend code is in this `frontend` directory
- Run all npm commands from this directory
- Backend is in `../python_backend` directory
- See main `README.md` in project root for full documentation
