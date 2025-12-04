/** Meetings List page with filtering and pagination. */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Link,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import WarningIcon from '@mui/icons-material/Warning';
import { meetingsApi, exportsApi } from '../services/api';

export default function MeetingsList() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    workgroup: '',
    source: '',
    date_from: '',
    date_to: '',
    search: '',
  });
  const [exporting, setExporting] = useState(false);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v)),
      };
      const response = await meetingsApi.list(params);
      setMeetings(response.data.items);
      setTotal(response.data.total);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, [page, pageSize]);

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
    setPage(1); // Reset to first page when filters change
  };

  const handleApplyFilters = () => {
    fetchMeetings();
  };

  const handleExport = async (format) => {
    try {
      setExporting(true);
      const response = await exportsApi.export({
        format,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v)),
      });
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `meetings_export.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to export');
    } finally {
      setExporting(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Ingested Meetings
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
          <TextField
            label="Workgroup"
            value={filters.workgroup}
            onChange={(e) => handleFilterChange('workgroup', e.target.value)}
            size="small"
          />
          <TextField
            label="Source"
            value={filters.source}
            onChange={(e) => handleFilterChange('source', e.target.value)}
            size="small"
          />
          <TextField
            label="Date From"
            type="date"
            value={filters.date_from}
            onChange={(e) => handleFilterChange('date_from', e.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Date To"
            type="date"
            value={filters.date_to}
            onChange={(e) => handleFilterChange('date_to', e.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Search (workgroup/title)"
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            size="small"
          />
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={handleApplyFilters}>
            Apply Filters
          </Button>
          <Button variant="outlined" onClick={() => setFilters({ workgroup: '', source: '', date_from: '', date_to: '', search: '' })}>
            Clear
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleExport('csv')}
            disabled={exporting}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleExport('json')}
            disabled={exporting}
          >
            Export JSON
          </Button>
        </Box>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Workgroup</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Meeting Date</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Warnings</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {meetings.map((meeting) => (
                  <TableRow key={meeting.id} hover>
                    <TableCell>
                      <Link component={RouterLink} to={`/meetings/${meeting.id}`}>
                        {meeting.id.substring(0, 8)}...
                      </Link>
                    </TableCell>
                    <TableCell>{meeting.workgroup || 'N/A'}</TableCell>
                    <TableCell>{meeting.source_name || 'N/A'}</TableCell>
                    <TableCell>{meeting.meeting_date || 'N/A'}</TableCell>
                    <TableCell>{meeting.title || 'N/A'}</TableCell>
                    <TableCell>
                      {meeting.validation_warnings_count > 0 && (
                        <Chip
                          icon={<WarningIcon />}
                          label={meeting.validation_warnings_count}
                          color="warning"
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      {meeting.has_missing_fields && (
                        <Chip label="Missing Fields" color="error" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={total}
            page={page - 1}
            onPageChange={(e, newPage) => setPage(newPage + 1)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(1);
            }}
            rowsPerPageOptions={[25, 50, 100]}
          />
        </>
      )}
    </Box>
  );
}

