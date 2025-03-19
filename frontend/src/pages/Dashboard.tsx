import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useDocumentStore } from '../stores/documentStore';
import { useAuthStore } from '../stores/authStore';
import { Navigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { stats, getCollectionStats, documents } = useDocumentStore();
  const { user } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      if (!user) return;
      
      setIsLoading(true);
      try {
        await getCollectionStats();
        setError(null);
      } catch (err: any) {
        console.error('Error fetching stats:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [user, getCollectionStats]);

  if (!user) {
    return <Navigate to="/login" />;
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="h6">Welcome, {user.username}!</Typography>
        
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
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Collection Statistics
                </Typography>
                {stats ? (
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography>Total Documents: {stats.total_documents}</Typography>
                      <Typography>Total Pages: {stats.total_pages}</Typography>
                      <Typography>Total Chunks: {stats.total_chunks}</Typography>
                      <Typography>Average Pages: {stats.average_pages.toFixed(2)}</Typography>
                      <Typography>
                        Average Chunks per Document: {stats.average_chunks_per_document.toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Document Status
                      </Typography>
                      <Typography>Completed: {stats.documents_by_status.completed}</Typography>
                      <Typography>Processing: {stats.documents_by_status.processing}</Typography>
                      <Typography>Failed: {stats.documents_by_status.failed}</Typography>
                    </Grid>
                  </Grid>
                ) : (
                  <Typography color="text.secondary">
                    No documents have been uploaded yet. Start by uploading some documents!
                  </Typography>
                )}
              </Paper>
            </Grid>
            {/* Statistics Cards */}
            <Grid item xs={12} md={4}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Total Documents
                </Typography>
                <Typography component="p" variant="h4">
                  {stats?.total_documents || 0}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Total Chunks
                </Typography>
                <Typography component="p" variant="h4">
                  {stats?.total_chunks || 0}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Average Chunks per Document
                </Typography>
                <Typography component="p" variant="h4">
                  {stats?.average_chunks_per_document?.toFixed(1) || 0}
                </Typography>
              </Paper>
            </Grid>

            {/* Recent Documents */}
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Recent Documents" />
                <CardContent>
                  <List>
                    {documents.slice(0, 5).map((doc, index) => (
                      <React.Fragment key={doc.id}>
                        <ListItem>
                          <ListItemText
                            primary={doc.filename}
                            secondary={`Uploaded: ${new Date(
                              doc.upload_date
                            ).toLocaleDateString()}`}
                          />
                        </ListItem>
                        {index < 4 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Box>
    </Container>
  );
}; 