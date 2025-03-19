import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { useDocumentStore } from '../stores/documentStore';
import { SearchResult } from '../api/client';

export const DocumentSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [includeProcessing, setIncludeProcessing] = useState(false);
  const { searchDocuments, searchResults, isLoading, error } = useDocumentStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await searchDocuments({
        query,
        similarity_threshold: similarityThreshold,
        include_processing: includeProcessing,
      });
    } catch (error) {
      console.error('Search error:', error);
      // Error is already handled in the store
    }
  };

  const renderSearchResult = (result: SearchResult) => (
    <Card key={result.document_id} sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {result.filename}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Score: {(result.similarity_score * 100).toFixed(1)}%
        </Typography>
        {result.matching_text && (
          <Typography variant="body1" sx={{ mt: 1 }}>
            {result.matching_text}
          </Typography>
        )}
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          Uploaded: {new Date(result.upload_date).toLocaleString()}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Search Documents
        </Typography>

        <Paper sx={{ p: 3, mb: 3 }}>
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Search Query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              margin="normal"
            />
            
            <Typography gutterBottom>
              Similarity Threshold: {similarityThreshold}
            </Typography>
            <Slider
              value={similarityThreshold}
              onChange={(_, value) => setSimilarityThreshold(value as number)}
              min={0}
              max={1}
              step={0.1}
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={includeProcessing}
                  onChange={(e) => setIncludeProcessing(e.target.checked)}
                />
              }
              label="Include Processing Documents"
            />

            <Box sx={{ mt: 2 }}>
              <Button
                type="submit"
                variant="contained"
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? 'Searching...' : 'Search'}
              </Button>
            </Box>
          </form>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          searchResults?.results?.map(renderSearchResult)
        )}
      </Box>
    </Container>
  );
}; 