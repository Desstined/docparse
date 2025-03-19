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
  CardHeader,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { useDocumentStore } from '../stores/documentStore';

export const DocumentSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const { searchDocuments, searchResults, isLoading, error } = useDocumentStore();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await searchDocuments({
        query,
        similarity_threshold: similarityThreshold,
        include_metadata: includeMetadata,
      });
    } catch (error) {
      // Error is handled by the document store
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Search Documents
        </Typography>

        {/* Search Form */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <form onSubmit={handleSearch}>
            <TextField
              fullWidth
              label="Search Query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              margin="normal"
              required
            />
            <Box sx={{ mt: 2 }}>
              <Typography gutterBottom>Similarity Threshold</Typography>
              <Slider
                value={similarityThreshold}
                onChange={(_, value) => setSimilarityThreshold(value as number)}
                min={0}
                max={1}
                step={0.1}
                marks
              />
              <Typography variant="body2" color="text.secondary">
                {Math.round(similarityThreshold * 100)}%
              </Typography>
            </Box>
            <FormControlLabel
              control={
                <Switch
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                />
              }
              label="Include Metadata"
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              sx={{ mt: 2 }}
              disabled={isLoading || !query}
            >
              {isLoading ? <CircularProgress size={24} /> : 'Search'}
            </Button>
          </form>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <Paper>
            <CardHeader title="Search Results" />
            <CardContent>
              <List>
                {searchResults.map((result, index) => (
                  <React.Fragment key={result.id}>
                    <ListItem>
                      <ListItemText
                        primary={result.document.filename}
                        secondary={
                          <>
                            <Typography
                              component="span"
                              variant="body2"
                              color="text.primary"
                            >
                              Similarity: {Math.round(result.similarity * 100)}%
                            </Typography>
                            <br />
                            <Typography
                              component="span"
                              variant="body2"
                              color="text.secondary"
                            >
                              {result.chunk.text}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    {index < searchResults.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Paper>
        )}
      </Box>
    </Container>
  );
}; 