/** Alerts panel component for recent failures and validation errors. */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert as MuiAlert,
  Button,
  Chip,
  CircularProgress,
  IconButton,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { alertsApi } from '../services/api';

export default function Alerts({ isAdmin = false }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertsApi.list({ hours: 24 });
      setAlerts(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Refresh every 2 minutes
    const interval = setInterval(fetchAlerts, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (alertId) => {
    try {
      await alertsApi.acknowledge(alertId);
      // Refresh alerts
      await fetchAlerts();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to acknowledge alert');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && alerts.length === 0) {
    return (
      <MuiAlert severity="error" sx={{ m: 2 }}>
        {error}
      </MuiAlert>
    );
  }

  if (alerts.length === 0) {
    return (
      <Card sx={{ m: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Alerts
          </Typography>
          <Typography color="textSecondary">
            No alerts in the last 24 hours. All systems operational.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Recent Alerts ({alerts.length})
      </Typography>
      {error && (
        <MuiAlert severity="warning" sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {alerts.map((alert) => (
          <Card key={alert.id} variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                    <Chip
                      label={alert.error_type}
                      color={alert.error_type === 'validation_error' ? 'warning' : 'error'}
                      size="small"
                    />
                    {alert.acknowledged && (
                      <Chip label="Acknowledged" color="success" size="small" icon={<CheckCircleIcon />} />
                    )}
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    {new Date(alert.timestamp).toLocaleString()}
                  </Typography>
                </Box>
                {isAdmin && !alert.acknowledged && (
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleAcknowledge(alert.id)}
                  >
                    Acknowledge
                  </Button>
                )}
              </Box>
              <Typography variant="body1" sx={{ mb: 1 }}>
                {alert.message}
              </Typography>
              {alert.source_url && (
                <Typography variant="body2" color="textSecondary">
                  Source: {alert.source_url}
                </Typography>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
}

