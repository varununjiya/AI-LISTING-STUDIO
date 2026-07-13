import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Package,
  FileEdit,
  CheckCircle2,
  Download,
  Plus,
  Search,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_STYLE = {
  draft: "bg-secondary text-secondary-foreground",
  completed: "bg-accent text-accent-foreground",
  exported: "bg-primary text-primary-foreground",
};

function StatCard({ icon: Icon, label, value, index, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.5 }}
      className="rounded-2xl border border-border bg-card p-6"
      data-testid={`stat-${label.toLowerCase().replace(/\s/g, "-")}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {loading ? (
        <Skeleton className="h-9 w-16" />
      ) : (
        <p className="font-heading font-black text-4xl tracking-tighter">{value}</p>
      )}
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

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, statusFilter]);

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Overview</p>
          <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Dashboard</h1>
        </div>
        <Button onClick={() => navigate("/products/new")} className="rounded-full font-semibold" data-testid="add-product-btn">
          <Plus className="mr-1 h-4 w-4" /> Add Product
        </Button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Package} label="Total Products" value={stats?.total ?? 0} index={0} loading={loading} />
        <StatCard icon={FileEdit} label="Draft Listings" value={stats?.draft ?? 0} index={1} loading={loading} />
        <StatCard icon={CheckCircle2} label="Completed Listings" value={stats?.completed ?? 0} index={2} loading={loading} />
        <StatCard icon={Download} label="Exported Listings" value={stats?.exported ?? 0} index={3} loading={loading} />
      </div>

      <div className="rounded-2xl border border-border bg-card">
        <div className="flex flex-wrap items-center justify-between gap-3 p-5 border-b border-border">
          <h2 className="font-heading font-bold text-lg">Recent Products</h2>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                data-testid="product-search-input"
                placeholder="Search products…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 w-48 sm:w-64 rounded-full"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36 rounded-full" data-testid="status-filter">
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
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
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="p-16 text-center">
            <p className="font-heading font-bold text-lg mb-2">No products yet</p>
            <p className="text-muted-foreground mb-6">Add your first product to generate AI listings.</p>
            <Button onClick={() => navigate("/products/new")} className="rounded-full" data-testid="empty-add-product-btn">
              <Plus className="mr-1 h-4 w-4" /> Add Product
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="hidden sm:table-cell">Brand</TableHead>
                <TableHead className="hidden md:table-cell">Category</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((p) => (
                <TableRow
                  key={p.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/products/${p.id}`)}
                  data-testid={`product-row-${p.id}`}
                >
                  <TableCell className="font-medium">{p.product_name}</TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">{p.brand || "—"}</TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground">{p.category || "—"}</TableCell>
                  <TableCell>
                    <Badge className={`${STATUS_STYLE[p.status]} capitalize rounded-full font-medium border-0`}>
                      {p.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{p.selling_price ? `₹${p.selling_price}` : "—"}</TableCell>
                  <TableCell className="text-right">
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground inline" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
