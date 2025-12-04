/** Trends page with time-series visualizations. */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { runsApi } from '../services/api';

export default function Trends() {
  const [monthlyData, setMonthlyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [months, setMonths] = useState(12);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await runsApi.getMonthly({ months });
        setMonthlyData(response.data.reverse()); // Show oldest to newest
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load trends');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [months]);

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

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Ingestion Trends
        </Typography>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Time Period</InputLabel>
          <Select value={months} onChange={(e) => setMonths(e.target.value)} label="Time Period">
            <MenuItem value={6}>Last 6 months</MenuItem>
            <MenuItem value={12}>Last 12 months</MenuItem>
            <MenuItem value={24}>Last 24 months</MenuItem>
            <MenuItem value={60}>Last 60 months</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {monthlyData.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="textSecondary">
              No trend data available. Start ingesting data to see trends.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Ingestion Volume Chart */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ingestion Volume per Month
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(value) => {
                      try {
                        const date = new Date(value);
                        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                      } catch {
                        return value;
                      }
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => {
                      try {
                        const date = new Date(value);
                        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
                      } catch {
                        return value;
                      }
                    }}
                  />
                  <Legend />
                  <Bar dataKey="records_ingested" fill="#8884d8" name="Records Ingested" />
                  <Bar dataKey="records_with_warnings" fill="#82ca9d" name="Records with Warnings" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Warning Rate Chart */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Warning Rate Trend
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(value) => {
                      try {
                        const date = new Date(value);
                        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                      } catch {
                        return value;
                      }
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => {
                      try {
                        const date = new Date(value);
                        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
                      } catch {
                        return value;
                      }
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="records_with_warnings"
                    stroke="#ff7300"
                    name="Records with Warnings"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
}

