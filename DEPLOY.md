# Deploy Guide

## Vercel Deployment

### Prerequisites
- Vercel CLI installed: `npm i -g vercel`
- GitHub repository connected to Vercel

### Deploy Steps

1. **Push to GitHub**:
```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

2. **Deploy to Vercel**:
```bash
vercel --prod
```

### Configuration Files

- `vercel.json`: Vercel configuration with Python runtime
- `requirements.txt`: Python dependencies (only `requests`)
- `python-api/pdf-to-elements.py`: Serverless function handler

### API Endpoints

- **Development**: `http://localhost:3001/api/pdf-to-elements`
- **Production**: `https://your-app.vercel.app/api/pdf-to-elements`

### Test Request

```bash
curl -X POST https://your-app.vercel.app/api/pdf-to-elements \
  -H "Content-Type: application/json" \
  -d '{"pdfUrl": "https://ais.airport.ir/documents/452631/166560064/OIYR.pdf"}'
```

### Troubleshooting

1. **Build Errors**: Check Vercel build logs
2. **Function Timeout**: Increase maxDuration in vercel.json
3. **Import Errors**: Ensure lib/ directory is included
4. **CORS Issues**: Headers are configured in Python function