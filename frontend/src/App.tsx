import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, CircularProgress } from '@mui/material';
import { theme } from './theme';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { DocumentUpload } from './pages/DocumentUpload';
import { DocumentSearch } from './pages/DocumentSearch';
import { useAuthStore } from './stores/authStore';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { token, user, loadUser, isLoading } = useAuthStore();
  
  useEffect(() => {
    if (token && !user) {
      loadUser();
    }
  }, [token]); // Remove user and loadUser from dependencies to prevent loops

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return token ? <>{children}</> : <Navigate to="/login" />;
};

export const App: React.FC = () => {
  return (
    <Router>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route path="upload" element={<DocumentUpload />} />
          <Route path="search" element={<DocumentSearch />} />
        </Routes>
      </ThemeProvider>
    </Router>
  );
};

export default App; 