import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

// Handles the Emergent OAuth redirect: reads session_id from the URL fragment,
// exchanges it for a persistent session cookie, then routes to the dashboard.
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? decodeURIComponent(match[1]) : null;

    const run = async () => {
      if (!sessionId) {
        navigate("/login", { replace: true });
        return;
      }
      try {
        const { data } = await api.post(
          "/auth/session",
          {},
          { headers: { "X-Session-ID": sessionId } }
        );
        setUser(data.user);
        window.history.replaceState(null, "", window.location.pathname);
        navigate("/dashboard", { replace: true, state: { user: data.user } });
      } catch {
        navigate("/login", { replace: true });
      }
    };
    run();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 rounded-full border-2 border-accent border-t-transparent animate-spin" />
        <p className="font-mono text-sm text-muted-foreground uppercase tracking-widest">
          Signing you in…
        </p>
      </div>
    </div>
  );
}
