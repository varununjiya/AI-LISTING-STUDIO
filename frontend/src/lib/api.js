import axios from "axios";

// Use the same origin when no backend URL is provided.
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

export const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;
