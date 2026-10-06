import axios from 'axios';
import { API_URL as API_BASE_URL } from '../config';

export const scanUrl = async (url, token) => {
  // Updated to support token if you haven't already
  const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};
  try {
    const response = await axios.post(`${API_BASE_URL}/scan`, { url }, config);
    return response.data;
  } catch (error) {
    console.error("Scanning Error:", error);
    throw error;
  }
};

// --- ADD THIS FUNCTION ---
export const fetchHistory = async (token) => {
  try {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    const response = await axios.get(`${API_BASE_URL}/history`, config);
    return response.data;
  } catch (error) {
    console.error("History Error:", error);
    throw error;
  }
};