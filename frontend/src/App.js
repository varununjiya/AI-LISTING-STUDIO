import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AuthCallback from "@/components/AuthCallback";
import DashboardLayout from "@/components/DashboardLayout";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Products from "@/pages/Products";
import AddProduct from "@/pages/AddProduct";
import ProductDetails from "@/pages/ProductDetails";
import BulkUpload from "@/pages/BulkUpload";
import Exports from "@/pages/Exports";
import Settings from "@/pages/Settings";

function AppRouter() {
  const location = useLocation();

  // Detect the OAuth session_id synchronously during render (before other routes),
  // preventing race conditions with the auth check.
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/new" element={<AddProduct />} />
        <Route path="/products/:id" element={<ProductDetails />} />
        <Route path="/products/:id/edit" element={<AddProduct />} />
        <Route path="/bulk-upload" element={<BulkUpload />} />
        <Route path="/exports" element={<Exports />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <div className="App">
        <BrowserRouter>
          <AuthProvider>
            <AppRouter />
            <Toaster position="top-right" richColors />
          </AuthProvider>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

export default App;
