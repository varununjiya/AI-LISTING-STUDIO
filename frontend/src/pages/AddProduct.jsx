import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Save, Sparkles, Upload, X, Loader2, ImageIcon, Wand2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Breadcrumbs from "@/components/Breadcrumbs";

const EMPTY = {
  brand: "", product_name: "", category: "", sub_category: "", material: "", color: "",
  size: "", weight: "", dimensions: "", capacity: "", features: "", benefits: "",
  usage_instructions: "", care_instructions: "", package_contents: "", mrp: "",
  selling_price: "", hsn_code: "", gst_percent: "", sku: "", model_number: "",
  country_of_origin: "", manufacturer: "", warranty: "", additional_notes: "", images: [],
};

const TEXT_FIELDS = [
  { key: "brand", label: "Brand" },
  { key: "product_name", label: "Product Name", required: true },
  { key: "category", label: "Category" },
  { key: "sub_category", label: "Sub Category" },
  { key: "material", label: "Material" },
  { key: "color", label: "Color" },
  { key: "size", label: "Size" },
  { key: "weight", label: "Weight" },
  { key: "dimensions", label: "Dimensions" },
  { key: "capacity", label: "Capacity" },
  { key: "sku", label: "SKU" },
  { key: "model_number", label: "Model Number" },
  { key: "mrp", label: "MRP" },
  { key: "selling_price", label: "Selling Price" },
  { key: "hsn_code", label: "HSN Code" },
  { key: "gst_percent", label: "GST %" },
  { key: "country_of_origin", label: "Country of Origin" },
  { key: "manufacturer", label: "Manufacturer" },
  { key: "warranty", label: "Warranty" },
];

const TEXTAREAS = [
  { key: "features", label: "Features" },
  { key: "benefits", label: "Benefits" },
  { key: "package_contents", label: "Package Contents" },
  { key: "usage_instructions", label: "Usage Instructions" },
  { key: "care_instructions", label: "Care Instructions" },
  { key: "additional_notes", label: "Additional Notes" },
];

export default function AddProduct() {
  const navigate = useNavigate();
  const { id } = useParams();
  const location = useLocation();
  const isEdit = location.pathname.endsWith("/edit");
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [productId, setProductId] = useState(id || null);

  useEffect(() => {
    if (isEdit && id) {
      api.get(`/products/${id}`).then(({ data }) => {
        setForm({ ...EMPTY, ...data.product });
        setProductId(id);
      });
    }
    // eslint-disable-next-line
  }, [id, isEdit]);

  const setField = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleImages = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => setForm((f) => ({ ...f, images: [...f.images, reader.result] }));
      reader.readAsDataURL(file);
    });
    e.target.value = "";
  };

  const removeImage = (idx) => setForm((f) => ({ ...f, images: f.images.filter((_, i) => i !== idx) }));

  const persist = async (status) => {
    const payload = { ...form };
    if (productId) {
      await api.put(`/products/${productId}`, payload);
      return productId;
    }
    const { data } = await api.post("/products", payload, { params: { status } });
    setProductId(data.id);
    return data.id;
  };

  const validate = () => {
    if (!form.product_name.trim()) {
      toast.error("Product Name is required");
      return false;
    }
    return true;
  };

  const handleAnalyze = async () => {
    if (form.images.length === 0) {
      toast.error("Upload a product image first");
      return;
    }
    if (!form.product_name.trim()) setField("product_name", "New Product");
    setAnalyzing(true);
    try {
      const pid = await persist("draft");
      const { data } = await api.post(`/products/${pid}/analyze-image`, { image: form.images[0], apply: true });
      const attrs = data.attributes || {};
      setForm((f) => {
        const merged = { ...f };
        Object.entries(attrs).forEach(([k, v]) => {
          if (k in EMPTY && v && (!merged[k] || merged[k] === "New Product")) merged[k] = v;
        });
        return merged;
      });
      toast.success("Fields auto-filled from image");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const pid = await persist("draft");
      toast.success(isEdit ? "Product updated" : "Draft saved");
      navigate(`/products/${pid}`);
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleGenerate = async () => {
    if (!validate()) return;
    setGenerating(true);
    try {
      const pid = await persist("draft");
      await api.post(`/products/${pid}/generate`);
      toast.success("Listing generated");
      navigate(`/products/${pid}?tab=amazon`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="pb-24" data-testid="add-product-page">
      <Breadcrumbs items={[{ label: "Dashboard", to: "/dashboard" }, { label: "Products", to: "/products" }, { label: isEdit ? "Edit" : "Add Product" }]} />
      <div className="mb-6">
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">{isEdit ? "Edit product" : "New product"}</p>
        <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">{isEdit ? "Edit Product" : "Add Product"}</h1>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-border bg-card p-6 sm:p-8 space-y-8">
        {/* Images first, with AI analyze */}
        <div className="space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <Label>Product Images</Label>
            <Button variant="outline" size="sm" onClick={handleAnalyze} disabled={analyzing || form.images.length === 0} className="rounded-full" data-testid="analyze-image-btn">
              {analyzing ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Wand2 className="mr-1 h-4 w-4" />}
              Auto-fill with AI
            </Button>
          </div>
          <div className="flex flex-wrap gap-3">
            {form.images.map((src, idx) => (
              <div key={idx} className="relative h-24 w-24 rounded-xl overflow-hidden border border-border group">
                <img src={src} alt="" className="h-full w-full object-cover" />
                <button onClick={() => removeImage(idx)} data-testid={`remove-image-${idx}`} className="absolute top-1 right-1 h-6 w-6 rounded-full bg-black/60 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
            <label className="h-24 w-24 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center gap-1 cursor-pointer hover:border-accent hover:bg-secondary transition-colors" data-testid="image-upload-label">
              <Upload className="h-5 w-5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Upload</span>
              <input type="file" accept="image/*" multiple className="hidden" onChange={handleImages} data-testid="image-upload-input" />
            </label>
          </div>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <ImageIcon className="h-3.5 w-3.5" /> Upload one image and click Auto-fill with AI to detect attributes.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 border-t border-border pt-6">
          {TEXT_FIELDS.map((f) => (
            <div key={f.key} className="space-y-2">
              <Label htmlFor={f.key}>{f.label} {f.required && <span className="text-destructive">*</span>}</Label>
              <Input id={f.key} data-testid={`field-${f.key}`} value={form[f.key]} onChange={(e) => setField(f.key, e.target.value)} placeholder={f.label} className="rounded-xl" />
            </div>
          ))}
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 border-t border-border pt-6">
          {TEXTAREAS.map((f) => (
            <div key={f.key} className="space-y-2">
              <Label htmlFor={f.key}>{f.label}</Label>
              <Textarea id={f.key} data-testid={`field-${f.key}`} value={form[f.key]} onChange={(e) => setField(f.key, e.target.value)} placeholder={f.label} rows={3} className="rounded-xl resize-none" />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Sticky action bar */}
      <div className="fixed bottom-0 inset-x-0 lg:pl-64 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-4">
          <div className="rounded-2xl border border-border bg-background/90 glass px-4 py-3 flex flex-wrap items-center justify-end gap-3 shadow-lg">
            <Button variant="outline" onClick={handleSaveDraft} disabled={saving || generating} className="rounded-full" data-testid="save-draft-btn">
              {saving ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Save className="mr-1 h-4 w-4" />}
              {isEdit ? "Save Changes" : "Save Draft"}
            </Button>
            <Button onClick={handleGenerate} disabled={saving || generating} className="rounded-full font-semibold" data-testid="generate-listing-btn">
              {generating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
              Generate Listing
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
