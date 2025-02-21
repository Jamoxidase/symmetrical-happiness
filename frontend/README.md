Dev:
    First you need npm.. brew install
    then in frontend/ run $ npm install
    this adds dependencies
    Then you can run $ npm run dev
    starts dev server with hot reloads
Dist:
    after making changes to project, run $ npm run build
    this updates dist/
    dist/ is ready to serve from dist/index
    only dist/ is needed for prod, make sure debug is off


# tRNA Analysis Chat Frontend

todo, make user bounce  to login if auth fails... its silent atm


A React-based frontend for the tRNA Analysis Chat application.

## Features

- Real-time chat interface with AI
- Dynamic data linking and visualization
- Interactive data explorer panel
- Responsive design with dark mode

## Data Linking System - backend default is no links

The application features a dynamic data linking system that connects chat responses with the data explorer:

### Link Format - Links are turned on or off via backend setting default off
Links in chat responses follow this format:
```
<gene_symbol/field_path>
```

Examples:
- Basic field: `<tRNA-Sec-TCA-1-1/GtRNAdb_Gene_Symbol>`
- Nested field: `<tRNA-Sec-TCA-1-1/sequences/Predicted Mature tRNA>`
- Image link: `<tRNA-Sec-TCA-1-1/images/cloverleaf>`

### Components

- `DataLink.jsx`: Handles parsing and rendering of data links
- `ArtifactsPanel.jsx`: Data explorer panel showing detailed sequence information
- `ChatInterface.jsx`: Main chat interface with message rendering

### Key Features

- Case-insensitive gene symbol matching
- Support for nested data fields
- Special handling for different data types (sequences, images, etc.)
- Automatic data explorer panel activation on data receipt

## Development

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start development server:
```bash
npm run dev
```

## Building for Production

```bash
npm run build
```

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)
- `VITE_WS_URL`: WebSocket URL if using WS (optional)
