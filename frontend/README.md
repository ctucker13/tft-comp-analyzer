# TFT Composition Analyzer - React/Next.js Frontend

Modern web interface for the TFT Composition Analyzer, built with React, Next.js 15, TypeScript, and Tailwind CSS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3001` (or `http://localhost:3000` if available).

## 🏗️ Architecture

### Frontend Stack
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Modern icon library

### API Integration
- **FastAPI Backend** - REST API at `http://localhost:8000`
- **Type-Safe APIs** - Full TypeScript definitions for all endpoints
- **Real-time Chat** - Strategic advice powered by LLM agents

## 📱 Features

### Chat Interface (`ChatInterface.tsx`)
- Real-time conversation with TFT AI advisor
- Message history and conversation tracking
- Intent detection and tool usage display
- Responsive design with typing indicators

### Meta Analysis (`MetaAnalysis.tsx`)
- S+ to C tier composition rankings
- Win rates, play rates, and average placements
- Recent trends analysis (7-day window)
- Filterable by tier with expandable details

### Champion Database (`DatabaseExplorer.tsx`)
- Complete Set 15 champion database (66 champions)
- Filter by name, cost, and traits
- Search functionality across champions and traits
- Cost-based color coding (1⭐ to 5⭐)

### ML Recommendations (`MLRecommendations.tsx`)
- Game state input (gold, level, stage, health)
- Quick scenario templates (Early Game, Mid Game, etc.)
- AI-powered strategic recommendations
- Confidence scoring and game phase detection

## 🎨 Design System

### TFT Theme
- **Primary Gold**: `#c89b3c` (Tailwind: `tft-gold`)
- **Dark Background**: Gradient from `#0a1428` to `#1e2328`
- **Tier Colors**: S+ (red), S (orange), A (yellow), B (green), C (gray)

### Components
- Responsive grid layouts
- Smooth animations and transitions
- Custom scrollbars
- Professional card-based UI

## 🛠️ Development

### File Structure
```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── globals.css   # Global styles and TFT theme
│   │   ├── layout.tsx    # Root layout component
│   │   └── page.tsx      # Main application page
│   ├── components/       # React components
│   │   ├── ChatInterface.tsx
│   │   ├── MetaAnalysis.tsx
│   │   ├── DatabaseExplorer.tsx
│   │   └── MLRecommendations.tsx
│   └── types/
│       └── api.ts        # TypeScript API definitions
├── public/               # Static assets
├── package.json
├── tailwind.config.js    # Tailwind configuration
└── tsconfig.json        # TypeScript configuration
```

### API Endpoints
- `/api/chat/message` - Send chat messages
- `/api/meta/tier-list` - Get tier lists
- `/api/meta/trends` - Get meta trends
- `/api/database/champions` - Champion database
- `/api/ml/recommend` - ML recommendations

### Environment Setup
The frontend expects the FastAPI backend to be running on `http://localhost:8000`. CORS is configured to allow requests from `localhost:3000` and `localhost:3001`.

## 🔧 Configuration

### Tailwind CSS
Custom configuration includes:
- TFT gold color (`#c89b3c`)
- Extended color palette for tiers
- Custom animations and transitions

### TypeScript
Strict type checking enabled with:
- Path aliases (`@/*` for `src/*`)
- React and Next.js type definitions
- Full API type coverage

## 🧪 Testing

Run the full-stack integration test:
```bash
# From project root
uv run python test_fullstack.py
```

## 📦 Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🤝 Integration with Backend

The frontend seamlessly integrates with the existing FastAPI backend:
- Reuses existing TFT analysis tools
- Maintains conversation context
- Provides real-time meta data
- Supports all ML recommendation features

For backend setup, see the main project README.md.