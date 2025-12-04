/** Meeting Detail page showing raw JSON, normalized fields, and warnings. */
import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Tabs,
  Tab,
  Paper,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningIcon from '@mui/icons-material/Warning';
import { meetingsApi } from '../services/api';

export default function MeetingDetail() {
  const { id } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        const response = await meetingsApi.getDetail(id);
        setMeeting(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load meeting detail');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchDetail();
    }
  }, [id]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !meeting) {
    return (
      <Box sx={{ p: 2 }}>
        <Button component={RouterLink} to="/meetings" startIcon={<ArrowBackIcon />}>
          Back to List
        </Button>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error || 'Meeting not found'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Button component={RouterLink} to="/meetings" startIcon={<ArrowBackIcon />} sx={{ mb: 2 }}>
        Back to List
      </Button>

      <Typography variant="h4" gutterBottom>
        Meeting Detail
      </Typography>

      {/* Summary Card */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {meeting.title || 'Untitled Meeting'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {meeting.workgroup && (
              <Chip label={`Workgroup: ${meeting.workgroup}`} />
            )}
            {meeting.source_name && (
              <Chip label={`Source: ${meeting.source_name}`} />
            )}
            {meeting.meeting_date && (
              <Chip label={`Date: ${meeting.meeting_date}`} />
            )}
            {meeting.validation_warnings && meeting.validation_warnings.length > 0 && (
              <Chip
                icon={<WarningIcon />}
                label={`${meeting.validation_warnings.length} Warnings`}
                color="warning"
              />
            )}
            {meeting.missing_fields && meeting.missing_fields.length > 0 && (
              <Chip
                label={`${meeting.missing_fields.length} Missing Fields`}
                color="error"
              />
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Tabs for different views */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(e, newValue) => setTab(newValue)}>
          <Tab label="Normalized Fields" />
          <Tab label="Validation Warnings" />
          <Tab label="Provenance" />
          {meeting.raw_json_reference && <Tab label="Raw JSON Reference" />}
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {tab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Normalized Fields
            </Typography>
            <pre style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px', overflow: 'auto' }}>
              {JSON.stringify(meeting.normalized_fields || {}, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Validation Warnings
            </Typography>
            {meeting.validation_warnings && meeting.validation_warnings.length > 0 ? (
              <Box>
                {meeting.validation_warnings.map((warning, idx) => (
                  <Accordion key={idx}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <WarningIcon color="warning" />
                        <Typography>
                          {warning.code || 'Warning'} - {warning.field_path || 'Unknown field'}
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography>{warning.message || 'No message'}</Typography>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            ) : (
              <Typography color="textSecondary">No validation warnings</Typography>
            )}
            {meeting.missing_fields && meeting.missing_fields.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Missing Mandatory Fields:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {meeting.missing_fields.map((field, idx) => (
                    <Chip key={idx} label={field} color="error" size="small" />
                  ))}
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Provenance
            </Typography>
            <pre style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px', overflow: 'auto' }}>
              {JSON.stringify(meeting.provenance || {}, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {tab === 3 && meeting.raw_json_reference && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Raw JSON Reference
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {meeting.raw_json_reference}
            </Typography>
            <Button
              variant="outlined"
              sx={{ mt: 2 }}
              onClick={() => window.open(meeting.raw_json_reference, '_blank')}
            >
              Open Raw JSON
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

