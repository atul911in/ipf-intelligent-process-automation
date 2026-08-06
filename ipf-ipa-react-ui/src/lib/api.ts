import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const endpoints = {
  upload: '/api/upload',
  uploadHistory: '/api/upload/history',
  status: (id: string) => '/api/status/' + id,
  queue: '/api/queue',
  review: (id: string) => '/api/review/' + id,
  correct: (id: string) => '/api/review/' + id + '/correct',
  confirm: (id: string) => '/api/review/' + id + '/confirm',
  preview: (id: string) => '/api/document/' + id + '/preview',
  decision: (id: string) => '/api/decision/' + id,
  audit: (id: string) => '/api/audit/' + id,
  creditScore: (id: string) => '/api/credit-score/' + id,
  loanApplication: (id: string) => '/api/loan-application/' + id,
  discrepancies: (id: string) => '/api/discrepancies/' + id,
  discrepancyOverride: (id: string) => '/api/discrepancies/' + id + '/override',
  health: '/api/health',
};
