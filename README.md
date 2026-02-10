# AIP PDF Reader

A Next.js application for parsing Aeronautical Information Publication (AIP) PDFs and extracting structured data.

## Features

- Upload and parse AIP PDFs
- Extract data from 5 different AD sections:
  - AD 2.1 - Location Indicator
  - AD 2.2 - Geographical Data
  - AD 2.10 - Obstacles
  - AD 2.12 - Runway Characteristics
  - AD 2.13 - Declared Distances
- Beautiful dark-themed UI with expandable tables
- Built with Next.js, TypeScript, and Tailwind CSS

## Setup

1. Install dependencies:
```bash
npm install
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run development server:
```bash
npm run dev
```

## Deployment to Vercel

1. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/mHn87/aip-pdf-reader.git
git push -u origin main
```

2. Connect to Vercel:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will automatically detect Next.js and Python functions
   - **For PDF parsing on Vercel:** In Project Settings → Environment Variables, add `UNSTRUCTURED_API_KEY` with your [Unstructured](https://platform.unstructured.io) API key.
   - Deploy!

## Project Structure

```
aip-pdf-reader/
├── app/                    # Next.js app directory
│   ├── api/                # Next.js API routes (TypeScript)
│   ├── page.tsx            # Main page
│   └── layout.tsx          # Root layout
├── api/                    # Python serverless functions (Vercel)
│   ├── upload.py           # PDF upload handler
│   └── parse/              # Parser endpoints
├── components/             # React components
│   ├── ui/                 # shadcn/ui components
│   ├── DataTables.tsx      # Data display component
│   ├── Navbar.tsx          # Navigation bar
│   └── PdfUploader.tsx     # PDF upload component
├── parser_ad2_*.py         # Python parsers
└── requirements.txt        # Python dependencies
```

## Notes

- For production, consider using Vercel KV or a database for storing uploaded PDF paths instead of environment variables
- The current implementation uses in-memory storage which won't work across multiple serverless function invocations
- For better state management, use Vercel KV or a similar service
