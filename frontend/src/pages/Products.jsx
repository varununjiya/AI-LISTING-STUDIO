import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, Trash2, ArrowUpRight } from "lucide-react";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const STATUS_STYLE = {
  draft: "bg-secondary text-secondary-foreground",
  completed: "bg-accent text-accent-foreground",
  exported: "bg-primary text-primary-foreground",
};

export default function Products() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [deleteId, setDeleteId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/products", {
        params: { search: search || undefined, status: statusFilter },
      });
      setProducts(data);
    } catch {
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, statusFilter]);

  const handleDelete = async () => {
    try {
      await api.delete(`/products/${deleteId}`);
      toast.success("Product deleted");
      setDeleteId(null);
      load();
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-8" data-testid="products-page">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Catalog</p>
          <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Products</h1>
        </div>
        <Button onClick={() => navigate("/products/new")} className="rounded-full font-semibold" data-testid="products-add-btn">
          <Plus className="mr-1 h-4 w-4" /> Add Product
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            data-testid="products-search-input"
            placeholder="Search by name, brand or category…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 rounded-full"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 rounded-full" data-testid="products-status-filter">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="exported">Exported</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-2xl border border-border bg-card">
        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="p-16 text-center">
            <p className="font-heading font-bold text-lg mb-2">No products found</p>
            <p className="text-muted-foreground mb-6">Try a different search or add a new product.</p>
            <Button onClick={() => navigate("/products/new")} className="rounded-full">
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
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((p) => (
                <TableRow key={p.id} data-testid={`product-row-${p.id}`}>
                  <TableCell
                    className="font-medium cursor-pointer"
                    onClick={() => navigate(`/products/${p.id}`)}
                  >
                    <span className="inline-flex items-center gap-1">
                      {p.product_name}
                      <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                    </span>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-muted-foreground">{p.brand || "—"}</TableCell>
                  <TableCell className="hidden md:table-cell text-muted-foreground">{p.category || "—"}</TableCell>
                  <TableCell>
                    <Badge className={`${STATUS_STYLE[p.status]} capitalize rounded-full font-medium border-0`}>
                      {p.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{p.selling_price ? `₹${p.selling_price}` : "—"}</TableCell>
                  <TableCell>
                    <button
                      onClick={() => setDeleteId(p.id)}
                      data-testid={`delete-product-${p.id}`}
                      className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-destructive/10 hover:text-destructive transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <AlertDialog open={!!deleteId} onOpenChange={(o) => !o && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this product?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the product and its generated listing.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} data-testid="confirm-delete-btn" className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
