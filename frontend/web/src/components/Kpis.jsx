/** KPI summary component for the ingestion dashboard. */
import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Grid, CircularProgress, Alert } from '@mui/material';
import { kpisApi } from '../services/api';

export default function Kpis() {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        setLoading(true);
        const response = await kpisApi.getKPIs();
        setKpis(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load KPIs');
      } finally {
        setLoading(false);
      }
    };

    fetchKPIs();
    // Refresh every 5 minutes
    const interval = setInterval(fetchKPIs, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat().format(num);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return `${num.toFixed(1)}%`;
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Operational Overview
      </Typography>
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Ingested
              </Typography>
              <Typography variant="h4">
                {formatNumber(kpis?.total_ingested)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Sources Processed
              </Typography>
              <Typography variant="h4">
                {formatNumber(kpis?.sources_count)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Success Rate
              </Typography>
              <Typography variant="h4" color={kpis?.success_rate >= 95 ? 'success.main' : 'warning.main'}>
                {formatPercentage(kpis?.success_rate)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Duplicates Avoided
              </Typography>
              <Typography variant="h4">
                {formatNumber(kpis?.duplicates_avoided)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Last Run
              </Typography>
              <Typography variant="h6">
                {formatDate(kpis?.last_run_timestamp)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

