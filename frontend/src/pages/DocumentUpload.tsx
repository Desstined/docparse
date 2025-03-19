import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Container,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Divider,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDocumentStore } from '../stores/documentStore';

export const DocumentUpload: React.FC = () => {
  const { uploadDocument, documents, deleteDocument, isLoading, error } =
    useDocumentStore();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        try {
          await uploadDocument(file);
        } catch (error) {
          // Error is handled by the document store
        }
      }
    },
    [uploadDocument]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  });

  const renderStatus = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'processing':
        return <CircularProgress size={24} />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Documents
        </Typography>

        {/* Dropzone */}
        <Paper
          {...getRootProps()}
          sx={{
            p: 3,
            mb: 3,
            textAlign: 'center',
            backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'divider',
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive
              ? 'Drop the files here'
              : 'Drag and drop PDF files here, or click to select files'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Only PDF files are supported
          </Typography>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Upload Progress */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Uploaded Documents List */}
        <Paper>
          <Typography variant="h6" sx={{ p: 2 }}>
            Uploaded Documents
          </Typography>
          <List>
            {documents.map((doc) => (
              <ListItem
                key={doc.id}
                secondaryAction={
                  <>
                    {renderStatus(doc.status)}
                    <IconButton 
                      edge="end" 
                      aria-label="delete"
                      onClick={() => deleteDocument(doc.id)}
                      disabled={doc.status === 'processing'}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </>
                }
              >
                <ListItemText
                  primary={doc.filename}
                  secondary={`Uploaded: ${new Date(doc.upload_date).toLocaleString()}`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </Container>
  );
}; 