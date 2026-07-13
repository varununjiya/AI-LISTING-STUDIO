import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Package, FileText, ImageIcon, Download, Plus, Search, ArrowUpRight,
  Gauge, Activity, Sparkles, Boxes, TrendingUp,
} from "lucide-react";
import { toast } from "sonner";
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as RTooltip,
  LineChart, Line, CartesianGrid, Legend,
} from "recharts";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const STATUS_STYLE = {
  draft: "bg-secondary text-secondary-foreground",
  completed: "bg-accent text-accent-foreground",
  exported: "bg-primary text-primary-foreground",
};

const PIE_COLORS = ["#4F46E5", "#E2FF54", "#22c55e", "#f97316", "#ec4899"];

function StatCard({ icon: Icon, label, value, index, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.5 }}
      className="rounded-2xl border border-border bg-card p-5"
      data-testid={`stat-${label.toLowerCase().replace(/\s/g, "-")}`}
    >
      <div className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
        <Icon className="h-5 w-5" />
      </div>
      {loading ? <Skeleton className="h-9 w-16" /> : <p className="font-heading font-black text-3xl tracking-tighter">{value}</p>}
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </motion.div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const load = async () => {
    setLoading(true);
    try {
      const [s, p] = await Promise.all([
        api.get("/stats"),
        api.get("/products", { params: { search: search || undefined, status: statusFilter } }),
      ]);
      setStats(s.data);
      setProducts(p.data);
    } catch {
      toast.error("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);
  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [search, statusFilter]);

  const dist = stats?.marketplace_distribution || {};
  const pieData = [
    { name: "Amazon", value: dist.amazon || 0 },
    { name: "Flipkart", value: dist.flipkart || 0 },
    { name: "Meesho", value: dist.meesho || 0 },
  ].filter((d) => d.value > 0);

  const catData = Object.entries(stats?.category_distribution || {})
    .map(([name, value]) => ({ name: name.length > 10 ? name.slice(0, 10) + "…" : name, value }))
    .slice(0, 6);

  const monthlyData = (stats?.monthly_trends || []).map(m => ({
    month: m.month ? new Date(m.month + "-01").toLocaleDateString('en-US', { month: 'short' }) : "",
    count: m.count || 0
  }));

  const avgQuality = stats?.avg_quality || 0;

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Overview</p>
          <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Dashboard</h1>
        </div>
        <Button onClick={() => navigate("/products/new")} className="rounded-full font-semibold" data-testid="add-product-btn">
          <Plus className="mr-1 h-4 w-4" /> Add Product
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Package} label="Total Products" value={stats?.total ?? 0} index={0} loading={loading} />
        <StatCard icon={FileText} label="Listings Generated" value={stats?.listings_generated ?? 0} index={1} loading={loading} />
        <StatCard icon={ImageIcon} label="Images Generated" value={stats?.images_generated ?? 0} index={2} loading={loading} />
        <StatCard icon={Download} label="Exports" value={stats?.exports_count ?? 0} index={3} loading={loading} />
      </div>

      {/* Analytics row */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Quality gauge */}
        <div className="rounded-2xl border border-border bg-card p-6 flex flex-col" data-testid="quality-card">
          <div className="flex items-center gap-2 mb-4">
            <Gauge className="h-4 w-4 text-accent" />
            <h3 className="font-heading font-bold text-sm">Avg Listing Quality</h3>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <div className="relative h-40 w-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={[{ value: avgQuality }, { value: 100 - avgQuality }]} innerRadius={58} outerRadius={72} startAngle={90} endAngle={-270} dataKey="value" stroke="none">
                    <Cell fill="#E2FF54" />
                    <Cell fill="hsl(var(--secondary))" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-heading font-black text-4xl">{avgQuality}</span>
                <span className="text-xs text-muted-foreground">/ 100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Marketplace distribution */}
        <div className="rounded-2xl border border-border bg-card p-6" data-testid="marketplace-card">
          <div className="flex items-center gap-2 mb-4">
            <Boxes className="h-4 w-4 text-accent" />
            <h3 className="font-heading font-bold text-sm">Marketplace Distribution</h3>
          </div>
          {pieData.length ? (
            <div className="flex items-center gap-4">
              <div className="h-40 w-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} innerRadius={40} outerRadius={72} paddingAngle={3} dataKey="value" stroke="none">
                      {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <RTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {pieData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2 text-sm">
                    <span className="h-3 w-3 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                    {d.name} <span className="text-muted-foreground">({d.value})</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground py-10 text-center">Generate listings to see distribution.</p>
          )}
        </div>

        {/* Recent activity */}
        <div className="rounded-2xl border border-border bg-card p-6" data-testid="activity-card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-4 w-4 text-accent" />
            <h3 className="font-heading font-bold text-sm">Recent Activity</h3>
          </div>
          <div className="space-y-3 max-h-44 overflow-y-auto">
            {stats?.recent_activity?.length ? stats.recent_activity.map((a) => (
              <div key={a.id} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-accent shrink-0" />
                <div>
                  <p className="leading-snug">{a.message}</p>
                  <p className="text-xs text-muted-foreground">{new Date(a.at).toLocaleString()}</p>
                </div>
              </div>
            )) : <p className="text-sm text-muted-foreground py-6 text-center">No activity yet.</p>}
          </div>
        </div>
      </div>

      {/* Monthly trends chart */}
      {monthlyData.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6" data-testid="monthly-trends-card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-accent" />
            <h3 className="font-heading font-bold text-sm">Monthly Trends (Last 6 Months)</h3>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} 
                  axisLine={false} 
                  tickLine={false} 
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} 
                  axisLine={false} 
                  tickLine={false} 
                />
                <RTooltip 
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem"
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#4F46E5" 
                  strokeWidth={3}
                  dot={{ fill: "#4F46E5", r: 5 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Category chart */}
      {catData.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6" data-testid="category-card">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-accent" />
            <h3 className="font-heading font-bold text-sm">Products by Category</h3>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={catData}>
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
                <RTooltip cursor={{ fill: "hsl(var(--secondary))" }} />
                <Bar dataKey="value" fill="#4F46E5" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent products */}
      <div className="rounded-2xl border border-border bg-card">
        <div className="flex flex-wrap items-center justify-between gap-3 p-5 border-b border-border">
          <h2 className="font-heading font-bold text-lg">Recent Products</h2>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input data-testid="product-search-input" placeholder="Search products…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9 w-48 sm:w-64 rounded-full" />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36 rounded-full" data-testid="status-filter"><SelectValue placeholder="Filter" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="exported">Exported</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="p-5 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
        ) : products.length === 0 ? (
          <div className="p-16 text-center">
            <p className="font-heading font-bold text-lg mb-2">No products yet</p>
            <p className="text-muted-foreground mb-6">Add your first product to generate AI listings.</p>
            <Button onClick={() => navigate("/products/new")} className="rounded-full" data-testid="empty-add-product-btn"><Plus className="mr-1 h-4 w-4" /> Add Product</Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="hidden sm:table-cell">Brand</TableHead>
                <TableHead className="hidden md:table-cell">Category</TableHead>
                <TableHead>Quality</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((p) => (
                <TableRow key={p.id} className="cursor-pointer" onClick={() => navigate(`/products/${p.id}`)} data-testid={`product-row-${p.id}`}>
                  <TableCell className="font-medium max-w-[240px] truncate">{p.product_name}</TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">{p.brand || "—"}</TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground">{p.category || "—"}</TableCell>
                  <TableCell>{p.quality_score ? <span className="font-semibold">{p.quality_score}</span> : <span className="text-muted-foreground">—</span>}</TableCell>
                  <TableCell><Badge className={`${STATUS_STYLE[p.status]} capitalize rounded-full font-medium border-0`}>{p.status}</Badge></TableCell>
                  <TableCell className="text-right"><ArrowUpRight className="h-4 w-4 text-muted-foreground inline" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
