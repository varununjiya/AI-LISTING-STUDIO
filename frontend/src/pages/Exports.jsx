import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Download, Loader2, FileSpreadsheet, ShoppingCart, Store, Boxes,
  ShoppingBag, FileJson, FileArchive, Package2,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import Breadcrumbs from "@/components/Breadcrumbs";

const EXPORT_TYPES = [
  { key: "amazon", label: "Amazon Excel", ext: "xlsx", desc: "Title, 5 bullets, description, backend keywords & search terms.", icon: ShoppingCart },
  { key: "flipkart", label: "Flipkart Excel", ext: "xlsx", desc: "Title, highlights, description & search keywords.", icon: Store },
  { key: "meesho", label: "Meesho Excel", ext: "xlsx", desc: "Title, highlights, description & discovery tags.", icon: Package2 },
  { key: "shopify", label: "Shopify CSV", ext: "csv", desc: "Product import CSV with handle, body & variants.", icon: ShoppingBag },
  { key: "woocommerce", label: "WooCommerce CSV", ext: "csv", desc: "WooCommerce product importer format.", icon: ShoppingBag },
  { key: "generic", label: "Generic Excel", ext: "xlsx", desc: "Full product + listing data, marketplace-agnostic.", icon: Boxes },
  { key: "json", label: "JSON Export", ext: "json", desc: "Structured JSON for developers & APIs.", icon: FileJson },
  { key: "zip", label: "ZIP with Images", ext: "zip", desc: "Generic Excel bundled with all generated images.", icon: FileArchive },
];

export default function Exports() {
  const [exports, setExports] = useState([]);
  const [busy, setBusy] = useState(null);

  const loadExports = async () => {
    try {
      const { data } = await api.get("/exports");
      setExports(data);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadExports();
  }, []);

  const handleExport = async (t) => {
    setBusy(t.key);
    try {
      const res = await api.post("/exports", { export_type: t.key }, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-listing-${t.key}.${t.ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${t.label} downloaded`);
      loadExports();
    } catch (e) {
      let msg = "Export failed";
      if (e?.response?.status === 400) {
        try {
          const text = await e.response.data.text();
          msg = JSON.parse(text).detail || "No products to export yet";
        } catch {
          msg = "No products to export yet";
        }
      }
      toast.error(msg);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-8" data-testid="exports-page">
      <div>
        <Breadcrumbs items={[{ label: "Dashboard", to: "/dashboard" }, { label: "Exports" }]} />
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Download</p>
        <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Exports</h1>
        <p className="text-muted-foreground mt-2">Generate marketplace-ready files across every channel.</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {EXPORT_TYPES.map((t, i) => (
          <motion.div
            key={t.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-2xl border border-border bg-card p-5 flex flex-col"
            data-testid={`export-card-${t.key}`}
          >
            <div className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center mb-3">
              <t.icon className="h-5 w-5" />
            </div>
            <h3 className="font-heading font-bold">{t.label}</h3>
            <p className="text-xs text-muted-foreground mt-1 flex-1">{t.desc}</p>
            <Button onClick={() => handleExport(t)} disabled={busy === t.key} className="rounded-full mt-4 font-semibold" size="sm" data-testid={`export-btn-${t.key}`}>
              {busy === t.key ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Download className="mr-1 h-4 w-4" />}
              Export
            </Button>
          </motion.div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card p-5">
        <h2 className="font-heading font-bold text-lg mb-4">Recent exports</h2>
        {exports.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No exports yet.</p>
        ) : (
          <div className="space-y-2">
            {exports.map((ex) => (
              <div key={ex.id} className="flex items-center justify-between rounded-xl border border-border px-4 py-3" data-testid={`export-history-${ex.id}`}>
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium capitalize">{ex.export_type} export</p>
                    <p className="text-xs text-muted-foreground">{ex.product_count} products · {new Date(ex.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground font-mono hidden sm:block">{ex.filename}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
