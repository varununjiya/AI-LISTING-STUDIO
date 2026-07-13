import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Copy,
  RefreshCw,
  Save,
  Sparkles,
  Loader2,
  Pencil,
  History as HistoryIcon,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const STATUS_STYLE = {
  draft: "bg-secondary text-secondary-foreground",
  completed: "bg-accent text-accent-foreground",
  exported: "bg-primary text-primary-foreground",
};

function EditableSection({ title, sectionKey, value, type = "textarea", productId, onUpdate }) {
  const initial = Array.isArray(value) ? value.join("\n") : value ?? "";
  const [draft, setDraft] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [regen, setRegen] = useState(false);

  useEffect(() => {
    setDraft(Array.isArray(value) ? value.join("\n") : value ?? "");
  }, [value]);

  const toPayloadValue = () =>
    Array.isArray(value) ? draft.split("\n").map((s) => s.trim()).filter(Boolean) : draft;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(draft);
    toast.success(`${title} copied`);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payloadVal = toPayloadValue();
      const { data } = await api.put(`/products/${productId}/listing`, { [sectionKey]: payloadVal });
      onUpdate(data);
      toast.success(`${title} saved`);
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setRegen(true);
    try {
      const { data } = await api.post(`/products/${productId}/regenerate/${sectionKey}`);
      const newVal = data.value;
      setDraft(Array.isArray(newVal) ? newVal.join("\n") : newVal ?? "");
      onUpdate((prev) => ({ ...prev, [sectionKey]: newVal }));
      toast.success(`${title} regenerated`);
    } catch {
      toast.error("Regenerate failed");
    } finally {
      setRegen(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5" data-testid={`section-${sectionKey}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading font-bold text-sm flex items-center gap-2">
          <Pencil className="h-3.5 w-3.5 text-accent" />
          {title}
        </h3>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="ghost" onClick={handleCopy} className="h-8 rounded-full px-3" data-testid={`copy-${sectionKey}`}>
            <Copy className="h-3.5 w-3.5" />
          </Button>
          <Button size="sm" variant="ghost" onClick={handleRegenerate} disabled={regen} className="h-8 rounded-full px-3" data-testid={`regen-${sectionKey}`}>
            {regen ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving} className="h-8 rounded-full px-3" data-testid={`save-${sectionKey}`}>
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </div>
      {type === "text" ? (
        <Input value={draft} onChange={(e) => setDraft(e.target.value)} className="rounded-xl" data-testid={`input-${sectionKey}`} />
      ) : (
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={Array.isArray(value) ? Math.max(5, value.length + 1) : 5}
          className="rounded-xl resize-none font-body"
          data-testid={`input-${sectionKey}`}
        />
      )}
      {Array.isArray(value) && (
        <p className="text-xs text-muted-foreground mt-2">One item per line.</p>
      )}
    </div>
  );
}

function GenerateEmptyState({ onGenerate, generating }) {
  return (
    <div className="rounded-2xl border border-dashed border-border p-12 text-center">
      <Sparkles className="h-8 w-8 mx-auto text-accent mb-4" />
      <p className="font-heading font-bold text-lg mb-2">No listing generated yet</p>
      <p className="text-muted-foreground mb-6">Generate an AI listing to review and edit it here.</p>
      <Button onClick={onGenerate} disabled={generating} className="rounded-full font-semibold" data-testid="generate-here-btn">
        {generating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
        Generate Listing
      </Button>
    </div>
  );
}

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [product, setProduct] = useState(null);
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [tab, setTab] = useState(searchParams.get("tab") || "info");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/products/${id}`);
      setProduct(data.product);
      setListing(data.listing);
    } catch {
      toast.error("Product not found");
      navigate("/products");
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    load();
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const { data } = await api.post(`/products/${id}/generate`);
      setListing(data);
      setProduct((p) => ({ ...p, status: "completed" }));
      toast.success("Listing generated");
      setTab("amazon");
    } catch {
      toast.error("Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const updateListing = (updater) =>
    setListing((prev) => (typeof updater === "function" ? updater(prev) : updater));

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const specEntries = Object.entries(product || {}).filter(
    ([k]) => !["id", "user_id", "status", "created_at", "updated_at", "images", "additional_notes"].includes(k)
  );

  return (
    <div className="space-y-6" data-testid="product-details-page">
      <button
        onClick={() => navigate("/products")}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        data-testid="back-btn"
      >
        <ArrowLeft className="h-4 w-4" /> Products
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <p className="font-mono text-xs uppercase tracking-widest text-accent">{product.brand || "Product"}</p>
            <Badge className={`${STATUS_STYLE[product.status]} capitalize rounded-full border-0`}>{product.status}</Badge>
          </div>
          <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">{product.product_name}</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate(`/products/${id}/edit`)} className="rounded-full" data-testid="edit-product-btn">
            <Pencil className="mr-1 h-4 w-4" /> Edit
          </Button>
          {listing && (
            <Button onClick={handleGenerate} disabled={generating} variant="outline" className="rounded-full" data-testid="regen-all-btn">
              {generating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-1 h-4 w-4" />}
              Regenerate All
            </Button>
          )}
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex flex-wrap h-auto gap-1 bg-secondary rounded-full p-1">
          <TabsTrigger value="info" className="rounded-full" data-testid="tab-info">Product Information</TabsTrigger>
          <TabsTrigger value="amazon" className="rounded-full" data-testid="tab-amazon">Amazon Listing</TabsTrigger>
          <TabsTrigger value="flipkart" className="rounded-full" data-testid="tab-flipkart">Flipkart Listing</TabsTrigger>
          <TabsTrigger value="seo" className="rounded-full" data-testid="tab-seo">SEO Keywords</TabsTrigger>
          <TabsTrigger value="history" className="rounded-full" data-testid="tab-history">History</TabsTrigger>
        </TabsList>

        {/* Product Information */}
        <TabsContent value="info" className="mt-6">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {product.images?.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {product.images.map((src, i) => (
                  <div key={i} className="h-28 w-28 rounded-xl overflow-hidden border border-border">
                    <img src={src} alt="" className="h-full w-full object-cover" />
                  </div>
                ))}
              </div>
            )}
            <div className="rounded-2xl border border-border bg-card p-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-5">
              {specEntries.map(([k, v]) => (
                <div key={k}>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{k.replace(/_/g, " ")}</p>
                  <p className="font-medium mt-0.5 break-words">{v || "—"}</p>
                </div>
              ))}
            </div>
            {product.additional_notes && (
              <div className="rounded-2xl border border-border bg-card p-6">
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Additional Notes</p>
                <p>{product.additional_notes}</p>
              </div>
            )}
          </motion.div>
        </TabsContent>

        {/* Amazon */}
        <TabsContent value="amazon" className="mt-6">
          {!listing ? (
            <GenerateEmptyState onGenerate={handleGenerate} generating={generating} />
          ) : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Amazon Title" sectionKey="amazon_title" value={listing.amazon_title} type="text" productId={id} onUpdate={updateListing} />
              <EditableSection title="Backend Keywords" sectionKey="amazon_backend_keywords" value={listing.amazon_backend_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Bullet Points (5)" sectionKey="amazon_bullets" value={listing.amazon_bullets} productId={id} onUpdate={updateListing} />
              <EditableSection title="Description" sectionKey="amazon_description" value={listing.amazon_description} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* Flipkart */}
        <TabsContent value="flipkart" className="mt-6">
          {!listing ? (
            <GenerateEmptyState onGenerate={handleGenerate} generating={generating} />
          ) : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Flipkart Title" sectionKey="flipkart_title" value={listing.flipkart_title} type="text" productId={id} onUpdate={updateListing} />
              <EditableSection title="Highlights" sectionKey="flipkart_highlights" value={listing.flipkart_highlights} productId={id} onUpdate={updateListing} />
              <EditableSection title="Description" sectionKey="flipkart_description" value={listing.flipkart_description} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* SEO */}
        <TabsContent value="seo" className="mt-6">
          {!listing ? (
            <GenerateEmptyState onGenerate={handleGenerate} generating={generating} />
          ) : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="SEO Keywords" sectionKey="seo_keywords" value={listing.seo_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Meta Description" sectionKey="meta_description" value={listing.meta_description} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* History */}
        <TabsContent value="history" className="mt-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            {listing?.history?.length ? (
              <ul className="space-y-4">
                {[...listing.history].reverse().map((h, i) => (
                  <li key={i} className="flex items-start gap-3" data-testid={`history-item-${i}`}>
                    <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                      <HistoryIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-medium capitalize">{h.action.replace(/[:_]/g, " ")}</p>
                      <p className="text-xs text-muted-foreground">{new Date(h.at).toLocaleString()}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground text-center py-8">No history yet.</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
