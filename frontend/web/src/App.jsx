import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';
import Kpis from './components/Kpis';
import Alerts from './components/Alerts';
import MeetingsList from './pages/MeetingsList';
import MeetingDetail from './pages/MeetingDetail';
import Trends from './pages/Trends';

function Navigation() {
  const location = useLocation();
  const isAdmin = true; // TODO: Get from auth context

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Ingestion Dashboard
        </Typography>
        <Button
          color="inherit"
          component={Link}
          to="/"
          variant={location.pathname === '/' ? 'outlined' : 'text'}
        >
          Overview
        </Button>
        <Button
          color="inherit"
          component={Link}
          to="/meetings"
          variant={location.pathname.startsWith('/meetings') ? 'outlined' : 'text'}
        >
          Meetings
        </Button>
        <Button
          color="inherit"
          component={Link}
          to="/trends"
          variant={location.pathname === '/trends' ? 'outlined' : 'text'}
        >
          Trends
        </Button>
      </Toolbar>
    </AppBar>
  );
}

function HomePage() {
  const isAdmin = true; // TODO: Get from auth context
  return (
    <Container maxWidth="xl">
      <Kpis />
      <Alerts isAdmin={isAdmin} />
    </Container>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Box sx={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        <Navigation />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/meetings" element={<MeetingsList />} />
          <Route path="/meetings/:id" element={<MeetingDetail />} />
          <Route path="/trends" element={<Trends />} />
        </Routes>
      </Box>
    </BrowserRouter>
  );
}
