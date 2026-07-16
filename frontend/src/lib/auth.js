const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function startGoogleLogin() {
  if (!window.google?.accounts?.oauth2) {
    console.error("Google Identity script not loaded yet — try again in a moment.");
    return;
  }
  const client = window.google.accounts.oauth2.initTokenClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: "openid email profile",
    callback: async (tokenResponse) => {
      if (tokenResponse.error) {
        console.error("Google login failed:", tokenResponse.error);
        return;
      }
      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ access_token: tokenResponse.access_token }),
        });
        if (!res.ok) {
          console.error("Backend rejected Google token");
          return;
        }
        window.location.href = "/dashboard";
      } catch (err) {
        console.error("Login request failed:", err);
      }
    },
  });
  client.requestAccessToken();
}

export async function logout() {
  await fetch(`${BACKEND_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  window.location.href = "/login";
}

export async function fetchCurrentUser() {
  const res = await fetch(`${BACKEND_URL}/api/auth/me`, {
    credentials: "include",
  });
  if (!res.ok) return null;
  return res.json();
}
