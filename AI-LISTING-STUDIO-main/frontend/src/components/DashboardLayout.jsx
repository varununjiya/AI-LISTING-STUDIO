import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  Upload,
  FileSpreadsheet,
  Settings as SettingsIcon,
  Boxes,
  Moon,
  Sun,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/products", label: "Products", icon: Package, testid: "nav-products" },
  { to: "/bulk-upload", label: "Bulk Upload", icon: Upload, testid: "nav-bulk-upload" },
  { to: "/exports", label: "Exports", icon: FileSpreadsheet, testid: "nav-exports" },
  { to: "/settings", label: "Settings", icon: SettingsIcon, testid: "nav-settings" },
];

function SidebarContent({ onNavigate }) {
  return (
    <div className="flex h-full flex-col">
      <NavLink to="/dashboard" className="flex items-center gap-2 px-6 h-16 border-b border-border" data-testid="sidebar-logo">
        <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
          <Boxes className="h-5 w-5 text-accent-foreground" />
        </div>
        <span className="font-heading font-extrabold text-xs tracking-tight">AI LISTING STUDIO</span>
      </NavLink>
      <nav className="flex-1 p-3 space-y-1">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            onClick={onNavigate}
            data-testid={item.testid}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 m-3 rounded-2xl bg-secondary">
        <p className="font-heading text-xs font-bold mb-1">AI Engine ready</p>
        <p className="text-xs text-muted-foreground">
          Configure your provider or bring your own key in Settings.
        </p>
      </div>
    </div>
  );
}

export default function DashboardLayout() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  const initials = (user?.name || user?.email || "U")
    .split(" ")
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 border-r border-border bg-card flex-col z-40">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-64 bg-card border-r border-border">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-4 h-8 w-8 flex items-center justify-center rounded-lg hover:bg-secondary"
              data-testid="sidebar-close"
            >
              <X className="h-4 w-4" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        {/* Topbar */}
        <header className="sticky top-0 z-30 h-16 border-b border-border bg-background/80 glass flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden h-9 w-9 flex items-center justify-center rounded-lg border border-border"
              data-testid="sidebar-open"
            >
              <Menu className="h-4 w-4" />
            </button>
            <span className="font-heading font-bold text-sm hidden sm:block">Workspace</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              data-testid="topbar-theme-toggle"
              className="h-9 w-9 rounded-full border border-border flex items-center justify-center hover:bg-secondary transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 rounded-full pl-1 pr-3 py-1 hover:bg-secondary transition-colors" data-testid="user-menu-trigger">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="text-xs bg-primary text-primary-foreground">{initials}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium hidden sm:block max-w-[120px] truncate">{user?.name || user?.email}</span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="truncate">{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/settings")} data-testid="menu-settings">
                  <SettingsIcon className="mr-2 h-4 w-4" /> Settings
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout} data-testid="menu-logout">
                  <LogOut className="mr-2 h-4 w-4" /> Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
