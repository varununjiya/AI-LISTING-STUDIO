import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Boxes, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { startGoogleLogin } from "@/lib/auth";

export default function Login() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) navigate("/dashboard", { replace: true });
  }, [user, loading, navigate]);

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-background text-foreground">
      {/* Left: brand panel */}
      <div className="relative hidden lg:flex flex-col justify-between p-12 bg-primary text-primary-foreground overflow-hidden grain">
        <div className="absolute -bottom-20 -left-20 h-80 w-80 rounded-full bg-accent/40 blur-3xl" />
        <a href="/" className="flex items-center gap-2 relative">
          <div className="h-9 w-9 rounded-lg bg-accent flex items-center justify-center">
            <Boxes className="h-5 w-5 text-accent-foreground" />
          </div>
          <span className="font-heading font-extrabold text-sm">AI LISTING STUDIO</span>
        </a>
        <div className="relative">
          <h1 className="font-heading font-black text-5xl xl:text-6xl leading-[0.95] tracking-tighter">
            Listings that outsmart the algorithm.
          </h1>
          <p className="mt-6 text-primary-foreground/80 max-w-sm">
            Generate Amazon &amp; Flipkart listings, bullet points, SEO keywords and
            exports — powered by AI.
          </p>
        </div>
        <p className="relative font-mono text-xs uppercase tracking-widest text-primary-foreground/60">
          E-commerce · AI · Automation
        </p>
      </div>

      {/* Right: login */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-10">
            <div className="h-9 w-9 rounded-lg bg-accent flex items-center justify-center">
              <Boxes className="h-5 w-5 text-accent-foreground" />
            </div>
            <span className="font-heading font-extrabold text-sm">AI LISTING STUDIO</span>
          </div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent mb-3">Welcome back</p>
          <h2 className="font-heading font-black text-3xl tracking-tight mb-3">Sign in to continue</h2>
          <p className="text-muted-foreground mb-8">
            Use your Google account to access your listing dashboard.
          </p>

          <Button
            data-testid="google-login-btn"
            onClick={startGoogleLogin}
            size="lg"
            className="w-full rounded-full h-14 text-base font-semibold"
          >
            Continue with Google
            <ArrowUpRight className="ml-1 h-5 w-5" />
          </Button>

          <p className="mt-6 text-xs text-muted-foreground text-center">
            By continuing you agree to the terms of service and privacy policy.
          </p>
          <button
            onClick={() => navigate("/")}
            data-testid="back-home-btn"
            className="mt-8 w-full text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  );
}
