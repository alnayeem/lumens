# Lumens Codebase Assessment

## Overview
**Lumens** is an open, multi-community catalog of public media (videos, podcasts) with transparent policies. The system ingests YouTube videos from curated channels, enriches them with metadata, stores them in Firestore, and serves them via a FastAPI backend to a React Native mobile app.

## Architecture

### 1. **Backend API (FastAPI)**
- **Location**: `apps/api/`
- **Technology**: Python 3.11, FastAPI, Firestore
- **Deployment**: Google Cloud Run
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /v1/content` - Get video content with pagination (supports filtering by topic, language, channel, made_for_kids)
  - `GET /v1/categories` - Get curated categories/topics
  - `GET /` - HTML web interface with video grid

### 2. **Data Ingestion Service**
- **Location**: `services/ingest/`
- **Technology**: Python, YouTube Data API v3
- **Features**:
  - Fetches videos from YouTube channels/playlists
  - Language detection and filtering
  - Enrichment with video metadata (duration, stats, thumbnails)
  - Firestore integration for persistent storage
  - Incremental ingest support (state tracking)
  - Channel resolution caching to optimize API quota

### 3. **Mobile App (React Native/Expo)**
- **Location**: `apps/mobile/`
- **Technology**: React Native, Expo SDK 54, TypeScript
- **Features**:
  - Authentication (Google OAuth)
  - Categories screen
  - Feed screen with infinite scroll
  - Swipe player screen (TikTok-style vertical scrolling)
  - Video player integration (react-native-youtube-iframe)

### 4. **Data Storage**
- **Database**: Google Cloud Firestore (Native mode)
- **Collections**:
  - `content/` - Video metadata
  - `channels/` - Channel information
  - `communities/` - Community configurations
  - `verticals/` - Vertical/category configurations
  - `policies/` - Policy documents

## Deployed Services

### API Server (Live)
**URL**: https://lumens-api-4qubw3p5lq-uc.a.run.app

**Endpoints**:
- Health: https://lumens-api-4qubw3p5lq-uc.a.run.app/health
- HTML Interface: https://lumens-api-4qubw3p5lq-uc.a.run.app/
- API Content: https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/content?language=en&limit=24
- Categories: https://lumens-api-4qubw3p5lq-uc.a.run.app/v1/categories

**Project**: `lumens-alnayeem-dev-02`
**Region**: `us-central1`
**Service Name**: `lumens-api`

### Current Status
✅ API is deployed and accessible
✅ Health endpoint responding
✅ Content endpoint returning video data
✅ Categories endpoint returning topic list

## Key Features

### Content Management
- **Topics/Categories**: prophets, duas, ramadan, seerah, nasheeds
- **Language Filtering**: English (en) with derived detection
- **Pagination**: Cursor-based pagination for efficient loading
- **Filtering**: By channel, topic, language, made_for_kids flag

### Video Enrichment
- Video duration
- View counts, likes, comments
- Thumbnails (multiple resolutions)
- Language detection with confidence scores
- English content filtering with fallback logic

### Mobile App Features
- **SwipePlayerScreen**: TikTok-style vertical video scrolling
- **FeedScreen**: Grid view with infinite scroll
- **CategoriesScreen**: Browse by topic
- **Authentication**: Google OAuth integration

## Data Flow

1. **Ingest**: 
   - CLI tool reads channel CSV
   - Fetches videos from YouTube API
   - Enriches with metadata
   - Stores in Firestore

2. **API**:
   - Queries Firestore based on filters
   - Decorates items with convenience fields (thumb, url, embed)
   - Returns paginated JSON

3. **Mobile**:
   - Fetches categories
   - Loads content by topic
   - Displays in feed or swipe player
   - Plays videos via YouTube embed

## Configuration

### Environment Variables
- `LUMENS_GCP_PROJECT`: GCP project ID (required for API)
- `LUMENS_YT_API_KEY`: YouTube Data API key (required for ingest)
- `API_BASE`: API base URL for mobile app
- `EXPO_PUBLIC_API_BASE`: Alternative API base for Expo

### Mobile App Configuration
- API base URL configured in `apps/mobile/app.config.js`
- Currently defaults to placeholder: `https://YOUR_CLOUD_RUN_URL`
- Should be set to: `https://lumens-api-4qubw3p5lq-uc.a.run.app`

## Deployment

### API Deployment
```bash
make deploy-api
# Or manually:
bash ./tools/deploy_api_service.sh -p lumens-alnayeem-dev-02 -r us-central1
```

### Ingest Job Deployment
```bash
make deploy-ingest
# Schedule with:
make schedule-ingest
```

## Current Issues & Recommendations

### 1. Mobile App API Configuration
**Issue**: Mobile app still has placeholder URL
**Fix**: Update `apps/mobile/app.config.js` or set `API_BASE` environment variable:
```bash
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
```

### 2. SwipePlayerScreen
- Currently has console.log for debugging (line 63)
- Consider removing or replacing with proper logging

### 3. Error Handling
- Mobile app has basic error handling
- Could benefit from retry logic and better error messages

### 4. Performance
- API uses Firestore indexes for efficient queries
- Consider caching for frequently accessed content
- Mobile app implements pagination for infinite scroll

## Testing

### Local API
```bash
export LUMENS_GCP_PROJECT=lumens-alnayeem-dev-02
make run-api
# Access at http://localhost:8000
```

### Local Ingest
```bash
export LUMENS_YT_API_KEY=your_key
make ingest LIMIT=25
```

### Mobile App
```bash
cd apps/mobile
export API_BASE=https://lumens-api-4qubw3p5lq-uc.a.run.app
npx expo start
```

## File Structure

```
lumens/
├── apps/
│   ├── api/              # FastAPI backend
│   └── mobile/           # React Native app
├── services/
│   ├── ingest/           # YouTube ingestion service
│   └── read/             # Firestore query utilities
├── data/
│   └── channels/         # Channel CSV files
├── tools/                # Deployment and setup scripts
├── policies/             # Policy YAML files
└── proto/                # Protobuf schemas
```

## Next Steps

1. ✅ Update mobile app API base URL
2. ✅ Remove debug console.log from SwipePlayerScreen
3. Consider adding analytics
4. Implement video caching for offline viewing
5. Add user preferences (favorites, watch history)
6. Implement search functionality
7. Add push notifications for new content

