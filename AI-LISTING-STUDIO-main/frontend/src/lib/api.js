import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Axios instance — always sends the session cookie for Emergent Google Auth.
const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;
