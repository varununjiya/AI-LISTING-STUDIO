import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Copy, RefreshCw, Save, Sparkles, Loader2, Pencil, History as HistoryIcon,
  Bot, CopyPlus, Gauge, RotateCcw, CheckCircle2, AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Breadcrumbs from "@/components/Breadcrumbs";
import AIImageStudio from "@/components/AIImageStudio";

const STATUS_STYLE = {
  draft: "bg-secondary text-secondary-foreground",
  completed: "bg-accent text-accent-foreground",
  exported: "bg-primary text-primary-foreground",
};

function EditableSection({ title, sectionKey, value, type = "textarea", limit, productId, onUpdate }) {
  const asStr = Array.isArray(value) ? value.join("\n") : value ?? "";
  const [draft, setDraft] = useState(asStr);
  const [saving, setSaving] = useState(false);
  const [regen, setRegen] = useState(false);

  useEffect(() => {
    setDraft(Array.isArray(value) ? value.join("\n") : value ?? "");
  }, [value]);

  const payloadValue = () => (Array.isArray(value) ? draft.split("\n").map((s) => s.trim()).filter(Boolean) : draft);
  const over = limit && draft.length > limit;

  const handleCopy = async () => { await navigator.clipboard.writeText(draft); toast.success(`${title} copied`); };
  const handleSave = async () => {
    setSaving(true);
    try {
      const { data } = await api.put(`/products/${productId}/listing`, { [sectionKey]: payloadValue() });
      onUpdate(data);
      toast.success(`${title} saved`);
    } catch { toast.error("Save failed"); } finally { setSaving(false); }
  };
  const handleRegenerate = async () => {
    setRegen(true);
    try {
      const { data } = await api.post(`/products/${productId}/regenerate/${sectionKey}`);
      const nv = data.value;
      setDraft(Array.isArray(nv) ? nv.join("\n") : nv ?? "");
      onUpdate((prev) => ({ ...prev, [sectionKey]: nv }));
      toast.success(`${title} regenerated`);
    } catch (e) { toast.error(e?.response?.data?.detail || "Regenerate failed"); } finally { setRegen(false); }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5" data-testid={`section-${sectionKey}`}>
      <div className="flex items-center justify-between mb-3 gap-2">
        <h3 className="font-heading font-bold text-sm flex items-center gap-2 min-w-0">
          <Pencil className="h-3.5 w-3.5 text-accent shrink-0" />
          <span className="truncate">{title}</span>
        </h3>
        <div className="flex items-center gap-1 shrink-0">
          <Button size="sm" variant="ghost" onClick={handleCopy} className="h-8 rounded-full px-3" data-testid={`copy-${sectionKey}`}><Copy className="h-3.5 w-3.5" /></Button>
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
        <Textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={Array.isArray(value) ? Math.max(5, value.length + 1) : 5} className="rounded-xl resize-none" data-testid={`input-${sectionKey}`} />
      )}
      <div className="flex items-center justify-between mt-2">
        {Array.isArray(value) ? <p className="text-xs text-muted-foreground">One item per line.</p> : <span />}
        {limit && (
          <p className={`text-xs font-mono ${over ? "text-destructive font-semibold" : "text-muted-foreground"}`} data-testid={`counter-${sectionKey}`}>
            {draft.length}/{limit}{over && " ⚠"}
          </p>
        )}
      </div>
    </div>
  );
}

function EmptyGen({ onGenerate, generating }) {
  return (
    <div className="rounded-2xl border border-dashed border-border p-12 text-center">
      <Sparkles className="h-8 w-8 mx-auto text-accent mb-4" />
      <p className="font-heading font-bold text-lg mb-2">No listing generated yet</p>
      <p className="text-muted-foreground mb-6">Generate AI listings to review and edit them here.</p>
      <Button onClick={onGenerate} disabled={generating} className="rounded-full font-semibold" data-testid="generate-here-btn">
        {generating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
        Generate Listing
      </Button>
    </div>
  );
}

const OVERVIEW_HIDE = ["id", "user_id", "status", "created_at", "updated_at", "images", "generated_images", "additional_notes", "quality_score"];

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [product, setProduct] = useState(null);
  const [listing, setListing] = useState(null);
  const [presets, setPresets] = useState([]);
  const [quality, setQuality] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [agentRunning, setAgentRunning] = useState(false);
  const [tab, setTab] = useState(searchParams.get("tab") || "overview");

  const load = useCallback(async () => {
    try {
      const [{ data }, q, v] = await Promise.all([
        api.get(`/products/${id}`),
        api.get(`/products/${id}/quality`).catch(() => ({ data: null })),
        api.get(`/products/${id}/versions`).catch(() => ({ data: { versions: [] } })),
      ]);
      setProduct(data.product);
      setListing(data.listing);
      setQuality(q.data);
      setVersions(v.data.versions || []);
    } catch {
      toast.error("Product not found");
      navigate("/products");
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    load();
    api.get("/image-presets").then(({ data }) => setPresets(data)).catch(() => {});
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const { data } = await api.post(`/products/${id}/generate`);
      setListing(data);
      await load();
      toast.success("Listing generated");
      setTab("amazon");
    } catch (e) { toast.error(e?.response?.data?.detail || "Generation failed"); } finally { setGenerating(false); }
  };

  const handleAgent = async () => {
    setAgentRunning(true);
    toast.info("AI Agent is analyzing, writing listings and generating images…");
    try {
      const { data } = await api.post(`/products/${id}/agent`, {});
      await load();
      toast.success(`AI Agent complete — quality score ${data.quality?.score ?? ""}`);
      setTab("amazon");
    } catch (e) { toast.error(e?.response?.data?.detail || "AI Agent failed"); } finally { setAgentRunning(false); }
  };

  const handleDuplicate = async () => {
    try {
      const { data } = await api.post(`/products/${id}/duplicate`);
      toast.success("Product duplicated");
      navigate(`/products/${data.id}`);
    } catch { toast.error("Duplicate failed"); }
  };

  const handleRestore = async (idx) => {
    try {
      const { data } = await api.post(`/products/${id}/restore/${idx}`);
      setListing(data);
      await load();
      toast.success("Version restored");
    } catch { toast.error("Restore failed"); }
  };

  const updateListing = (updater) => setListing((prev) => (typeof updater === "function" ? updater(prev) : updater));

  if (loading) {
    return <div className="space-y-6"><Skeleton className="h-8 w-48" /><Skeleton className="h-64 w-full" /></div>;
  }

  const overviewEntries = Object.entries(product || {}).filter(([k, v]) => !OVERVIEW_HIDE.includes(k) && v);

  return (
    <div className="pb-24 space-y-6" data-testid="product-details-page">
      <Breadcrumbs items={[{ label: "Dashboard", to: "/dashboard" }, { label: "Products", to: "/products" }, { label: product.product_name }]} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <p className="font-mono text-xs uppercase tracking-widest text-accent">{product.brand || "Product"}</p>
            <Badge className={`${STATUS_STYLE[product.status]} capitalize rounded-full border-0`}>{product.status}</Badge>
            {product.quality_score > 0 && (
              <Badge variant="outline" className="rounded-full gap-1"><Gauge className="h-3 w-3" /> {product.quality_score}/100</Badge>
            )}
          </div>
          <h1 className="font-heading font-black text-2xl sm:text-3xl lg:text-4xl tracking-tight break-words max-w-2xl">{product.product_name}</h1>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" onClick={handleDuplicate} className="rounded-full" data-testid="duplicate-btn"><CopyPlus className="mr-1 h-4 w-4" /> Duplicate</Button>
          <Button variant="outline" onClick={() => navigate(`/products/${id}/edit`)} className="rounded-full" data-testid="edit-product-btn"><Pencil className="mr-1 h-4 w-4" /> Edit</Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex flex-wrap h-auto gap-1 bg-secondary rounded-2xl p-1">
          {[
            ["overview", "Overview"], ["images", "Images"], ["studio", "AI Image Studio"],
            ["amazon", "Amazon"], ["flipkart", "Flipkart"], ["meesho", "Meesho"],
            ["seo", "SEO"], ["analytics", "Analytics"], ["history", "History"],
          ].map(([v, l]) => (
            <TabsTrigger key={v} value={v} className="rounded-xl text-xs sm:text-sm" data-testid={`tab-${v}`}>{l}</TabsTrigger>
          ))}
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="mt-6">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-border bg-card p-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-5">
            {overviewEntries.map(([k, v]) => (
              <div key={k}>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{k.replace(/_/g, " ")}</p>
                <p className="font-medium mt-0.5 break-words">{String(v)}</p>
              </div>
            ))}
          </motion.div>
          {product.additional_notes && (
            <div className="rounded-2xl border border-border bg-card p-6 mt-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Additional Notes</p>
              <p>{product.additional_notes}</p>
            </div>
          )}
        </TabsContent>

        {/* Images (uploaded) */}
        <TabsContent value="images" className="mt-6">
          {product.images?.length ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {product.images.map((src, i) => (
                <div key={i} className="rounded-xl overflow-hidden border border-border">
                  <img src={src} alt="" className="w-full aspect-square object-cover" />
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-border p-12 text-center">
              <p className="text-muted-foreground">No uploaded images. Edit the product to add images.</p>
            </div>
          )}
        </TabsContent>

        {/* AI Image Studio */}
        <TabsContent value="studio" className="mt-6">
          <AIImageStudio productId={id} product={product} presets={presets} onUpdate={load} />
        </TabsContent>

        {/* Amazon */}
        <TabsContent value="amazon" className="mt-6">
          {!listing ? <EmptyGen onGenerate={handleGenerate} generating={generating} /> : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Amazon Title" sectionKey="amazon_title" value={listing.amazon_title} type="text" limit={200} productId={id} onUpdate={updateListing} />
              <EditableSection title="Backend Keywords" sectionKey="amazon_backend_keywords" value={listing.amazon_backend_keywords} limit={250} productId={id} onUpdate={updateListing} />
              <EditableSection title="Bullet Points (5)" sectionKey="amazon_bullets" value={listing.amazon_bullets} productId={id} onUpdate={updateListing} />
              <EditableSection title="Description" sectionKey="amazon_description" value={listing.amazon_description} limit={2000} productId={id} onUpdate={updateListing} />
              <EditableSection title="Search Terms" sectionKey="amazon_search_terms" value={listing.amazon_search_terms} productId={id} onUpdate={updateListing} />
              <EditableSection title="A+ Content Suggestions" sectionKey="amazon_aplus_suggestions" value={listing.amazon_aplus_suggestions} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* Flipkart */}
        <TabsContent value="flipkart" className="mt-6">
          {!listing ? <EmptyGen onGenerate={handleGenerate} generating={generating} /> : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Flipkart Title" sectionKey="flipkart_title" value={listing.flipkart_title} type="text" limit={150} productId={id} onUpdate={updateListing} />
              <EditableSection title="Highlights" sectionKey="flipkart_highlights" value={listing.flipkart_highlights} productId={id} onUpdate={updateListing} />
              <EditableSection title="Description" sectionKey="flipkart_description" value={listing.flipkart_description} limit={2000} productId={id} onUpdate={updateListing} />
              <EditableSection title="Search Keywords" sectionKey="flipkart_search_keywords" value={listing.flipkart_search_keywords} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* Meesho */}
        <TabsContent value="meesho" className="mt-6">
          {!listing ? <EmptyGen onGenerate={handleGenerate} generating={generating} /> : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Meesho Title" sectionKey="meesho_title" value={listing.meesho_title} type="text" limit={120} productId={id} onUpdate={updateListing} />
              <EditableSection title="Highlights" sectionKey="meesho_highlights" value={listing.meesho_highlights} productId={id} onUpdate={updateListing} />
              <EditableSection title="Description" sectionKey="meesho_description" value={listing.meesho_description} limit={1500} productId={id} onUpdate={updateListing} />
              <EditableSection title="Tags" sectionKey="meesho_tags" value={listing.meesho_tags} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* SEO */}
        <TabsContent value="seo" className="mt-6">
          {!listing ? <EmptyGen onGenerate={handleGenerate} generating={generating} /> : (
            <div className="grid lg:grid-cols-2 gap-4">
              <EditableSection title="Primary Keywords" sectionKey="seo_primary_keywords" value={listing.seo_primary_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Secondary Keywords" sectionKey="seo_secondary_keywords" value={listing.seo_secondary_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Long-tail Keywords" sectionKey="seo_long_tail_keywords" value={listing.seo_long_tail_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Trending Keywords" sectionKey="seo_trending_keywords" value={listing.seo_trending_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Competitor Keywords" sectionKey="seo_competitor_keywords" value={listing.seo_competitor_keywords} productId={id} onUpdate={updateListing} />
              <EditableSection title="Meta Description" sectionKey="meta_description" value={listing.meta_description} limit={160} productId={id} onUpdate={updateListing} />
            </div>
          )}
        </TabsContent>

        {/* Analytics */}
        <TabsContent value="analytics" className="mt-6 space-y-4">
          <div className="rounded-2xl border border-border bg-card p-6" data-testid="quality-breakdown">
            <div className="flex items-center gap-2 mb-4"><Gauge className="h-4 w-4 text-accent" /><h3 className="font-heading font-bold">Listing Quality Score</h3></div>
            <div className="flex items-center gap-6 flex-wrap">
              <div className="font-heading font-black text-6xl tracking-tighter">{quality?.score ?? 0}<span className="text-xl text-muted-foreground">/100</span></div>
              <div className="flex-1 min-w-[240px] space-y-2">
                {Object.entries(quality?.breakdown || {}).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-3">
                    <span className="text-sm capitalize w-40 text-muted-foreground">{k.replace(/_/g, " ")}</span>
                    <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-accent" style={{ width: `${Math.min(100, (v / 25) * 100)}%` }} />
                    </div>
                    <span className="text-sm font-medium w-8 text-right">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {quality?.suggestions?.length > 0 && (
            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="font-heading font-bold mb-3 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-accent" /> Suggestions</h3>
              <ul className="space-y-2">
                {quality.suggestions.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm"><span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-accent shrink-0" />{s}</li>
                ))}
              </ul>
            </div>
          )}
        </TabsContent>

        {/* History */}
        <TabsContent value="history" className="mt-6 space-y-4">
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="font-heading font-bold mb-4">Activity</h3>
            {listing?.history?.length ? (
              <ul className="space-y-4">
                {[...listing.history].reverse().map((h, i) => (
                  <li key={i} className="flex items-start gap-3" data-testid={`history-item-${i}`}>
                    <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0"><HistoryIcon className="h-4 w-4" /></div>
                    <div>
                      <p className="font-medium capitalize">{h.action.replace(/[:_]/g, " ")}</p>
                      <p className="text-xs text-muted-foreground">{new Date(h.at).toLocaleString()}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : <p className="text-muted-foreground text-center py-8">No history yet.</p>}
          </div>

          {versions.length > 0 && (
            <div className="rounded-2xl border border-border bg-card p-6">
              <h3 className="font-heading font-bold mb-4">Previous Versions ({versions.length})</h3>
              <div className="space-y-2">
                {versions.map((v, i) => (
                  <div key={i} className="flex items-center justify-between rounded-xl border border-border px-4 py-3" data-testid={`version-${i}`}>
                    <div>
                      <p className="font-medium text-sm truncate max-w-md">{v.snapshot?.amazon_title || "Version " + (i + 1)}</p>
                      <p className="text-xs text-muted-foreground">{new Date(v.created_at).toLocaleString()}</p>
                    </div>
                    <Button size="sm" variant="outline" onClick={() => handleRestore(i)} className="rounded-full" data-testid={`restore-${i}`}>
                      <RotateCcw className="mr-1 h-3.5 w-3.5" /> Restore
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Sticky action bar */}
      <div className="fixed bottom-0 inset-x-0 lg:pl-64 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-4">
          <div className="rounded-2xl border border-border bg-background/90 glass px-4 py-3 flex flex-wrap items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center gap-2 text-sm">
              {listing ? <CheckCircle2 className="h-4 w-4 text-accent" /> : <AlertTriangle className="h-4 w-4 text-muted-foreground" />}
              <span className="text-muted-foreground">{listing ? "Listing ready" : "No listing yet"}</span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Button onClick={handleAgent} disabled={agentRunning} className="rounded-full font-semibold bg-primary" data-testid="run-agent-btn">
                {agentRunning ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Bot className="mr-1 h-4 w-4" />}
                Run AI Agent
              </Button>
              <Button variant="outline" onClick={handleGenerate} disabled={generating} className="rounded-full" data-testid="generate-sticky-btn">
                {generating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
                {listing ? "Regenerate" : "Generate"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
