# Document Parser Frontend

A modern React application for uploading, processing, and searching PDF documents. Built with TypeScript, Material-UI, and Zustand.

## Features

- User authentication with JWT
- PDF document upload with drag-and-drop support
- Document processing status tracking
- Semantic search across processed documents
- Responsive design for all screen sizes
- Real-time updates and progress indicators

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Backend API running (see main project README)

## Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```

## Development

Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Building for Production

Build the application:
```bash
npm run build
```

The production build will be created in the `build` directory.

## Testing

Run the test suite:
```bash
npm test
```

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and types
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components
│   ├── stores/        # Zustand state management
│   ├── theme.ts       # Material-UI theme configuration
│   └── App.tsx        # Main application component
├── public/            # Static assets
├── package.json       # Dependencies and scripts
└── tsconfig.json      # TypeScript configuration
```

## Environment Variables

Create a `.env` file in the frontend directory with the following variables:

```
REACT_APP_API_URL=http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 