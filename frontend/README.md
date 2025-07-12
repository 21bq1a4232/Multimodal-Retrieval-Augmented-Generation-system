# Multimodal RAG System Frontend

A modern React frontend for the Multimodal Retrieval Augmented Generation system. This frontend provides an intuitive interface for uploading documents, querying the knowledge base, and managing your documents.

## Features

- **Dashboard**: Overview of system status and quick actions
- **Document Upload**: Drag-and-drop PDF upload with real-time progress tracking
- **Query Interface**: Natural language question answering with citations
- **Document Management**: View, monitor, and manage uploaded documents
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Feedback**: Toast notifications and loading states
- **Modern UI**: Built with Tailwind CSS and Lucide React icons

## Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000` (or set `REACT_APP_API_URL` environment variable)

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`.

## Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Available Scripts

- `npm start` - Start the development server
- `npm build` - Build the application for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (not recommended)

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── Navbar.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── DocumentUpload.tsx
│   │   ├── QueryInterface.tsx
│   │   └── Documents.tsx
│   ├── services/
│   │   └── apiService.ts
│   ├── App.tsx
│   ├── index.tsx
│   └── index.css
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## Usage

### Dashboard
- View system statistics and health status
- Access quick actions for common tasks
- Monitor recent activity

### Document Upload
- Drag and drop PDF files or click to select
- Real-time upload progress tracking
- Automatic processing and indexing
- Support for files up to 50MB

### Query Interface
- Ask natural language questions about your documents
- View AI-generated answers with confidence scores
- See source citations with page numbers
- Provide feedback to improve system accuracy
- View query history

### Document Management
- Browse all uploaded documents
- Monitor processing status
- View document details (pages, chunks, file size)
- Delete documents when no longer needed

## API Integration

The frontend communicates with the backend API through the `apiService.ts` module, which handles:

- Authentication with Bearer tokens
- Document upload and status monitoring
- Query processing and response handling
- Feedback submission
- System statistics retrieval

## Styling

The application uses Tailwind CSS for styling with:

- Custom color scheme (primary blues, secondary grays)
- Responsive design patterns
- Consistent component styling
- Smooth animations and transitions

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Adding New Features

1. Create new components in the `components/` directory
2. Add new pages in the `pages/` directory
3. Update routing in `App.tsx`
4. Add API methods to `apiService.ts` if needed

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow the established color scheme
- Maintain consistent spacing and typography
- Ensure responsive design for all components

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Ensure the backend is running and accessible
2. **CORS Issues**: The backend should have CORS configured for the frontend domain
3. **Authentication Errors**: Check that the demo token is being sent correctly

### Debug Mode

Enable debug mode by setting the environment variable:
```env
REACT_APP_DEBUG=true
```

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for all new interfaces
3. Include error handling for API calls
4. Test responsive design on different screen sizes
5. Update documentation for new features

## License

This project is part of the Multimodal RAG System and follows the same license terms. 