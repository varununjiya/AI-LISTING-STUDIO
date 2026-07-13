import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Download, Trash2, Wand2, FileArchive, ImagePlus, Sparkles } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

const GROUP_LABELS = {
  studio: "Studio Shots",
  lifestyle: "Lifestyle Scenes",
  commerce: "Commerce & Infographics",
  social: "Social & Marketing",
};

function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export default function AIImageStudio({ productId, product, presets, onUpdate }) {
  const images = product.images || [];
  const generated = product.generated_images || [];
  const [sourceIdx, setSourceIdx] = useState(0);
  const [selected, setSelected] = useState([]);
  const [customPrompt, setCustomPrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const grouped = presets.reduce((acc, p) => {
    (acc[p.group] = acc[p.group] || []).push(p);
    return acc;
  }, {});

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const generateOne = async (body) => {
    return api.post(`/products/${productId}/images/generate`, { source_index: sourceIdx, ...body });
  };

  const handleGenerateSelected = async () => {
    if (images.length === 0) return toast.error("Upload a product image first");
    if (selected.length === 0) return toast.error("Select at least one style");
    setRunning(true);
    setProgress(0);
    let done = 0;
    let failed = 0;
    for (const presetId of selected) {
      try {
        await generateOne({ preset_id: presetId });
      } catch (e) {
        failed += 1;
        toast.error(e?.response?.data?.detail || `Failed: ${presetId}`);
        if ((e?.response?.data?.detail || "").toLowerCase().includes("budget")) break;
      }
      done += 1;
      setProgress(Math.round((done / selected.length) * 100));
    }
    setRunning(false);
    setSelected([]);
    if (done - failed > 0) toast.success(`Generated ${done - failed} image(s)`);
    onUpdate();
  };

  const handleCustom = async () => {
    if (images.length === 0) return toast.error("Upload a product image first");
    if (!customPrompt.trim()) return toast.error("Enter a prompt");
    setRunning(true);
    try {
      await generateOne({ prompt: customPrompt, label: "Custom" });
      toast.success("Custom image generated");
      setCustomPrompt("");
      onUpdate();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Generation failed");
    } finally {
      setRunning(false);
    }
  };

  const handleDelete = async (imgId) => {
    await api.delete(`/products/${productId}/images/${imgId}`);
    onUpdate();
  };

  const handleZip = async () => {
    try {
      const res = await api.get(`/products/${productId}/images/zip`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      downloadDataUrl(url, "product_images.zip");
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("No images to download");
    }
  };

  if (images.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border p-12 text-center">
        <ImagePlus className="h-8 w-8 mx-auto text-accent mb-4" />
        <p className="font-heading font-bold text-lg mb-2">No source image</p>
        <p className="text-muted-foreground">Add a product image (edit the product) to use AI Image Studio.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="ai-image-studio">
      {/* Source selector */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <p className="font-heading font-bold text-sm mb-3">Source image</p>
        <div className="flex flex-wrap gap-3">
          {images.map((src, i) => (
            <button
              key={i}
              onClick={() => setSourceIdx(i)}
              data-testid={`source-image-${i}`}
              className={`h-20 w-20 rounded-xl overflow-hidden border-2 transition-colors ${sourceIdx === i ? "border-accent" : "border-border"}`}
            >
              <img src={src} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      </div>

      {/* Preset groups */}
      {Object.entries(grouped).map(([group, list]) => (
        <div key={group} className="rounded-2xl border border-border bg-card p-5">
          <p className="font-heading font-bold text-sm mb-4">{GROUP_LABELS[group] || group}</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {list.map((p) => (
              <button
                key={p.id}
                onClick={() => toggle(p.id)}
                data-testid={`preset-${p.id}`}
                className={`text-left rounded-xl border px-3 py-2.5 text-sm transition-colors ${
                  selected.includes(p.id) ? "border-accent bg-accent/10 text-foreground" : "border-border hover:bg-secondary text-muted-foreground"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      ))}

      {/* Custom prompt */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <p className="font-heading font-bold text-sm mb-3">Custom scene</p>
        <div className="flex gap-2">
          <Input value={customPrompt} onChange={(e) => setCustomPrompt(e.target.value)} placeholder="e.g. product on a marble countertop with morning light" className="rounded-xl" data-testid="custom-prompt-input" />
          <Button onClick={handleCustom} disabled={running} className="rounded-full shrink-0" data-testid="custom-generate-btn">
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Generate action */}
      <div className="sticky bottom-4 z-20">
        <div className="rounded-2xl border border-border bg-background/90 glass p-4 shadow-lg">
          {running && <Progress value={progress} className="mb-3 h-2" data-testid="image-progress" />}
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">{selected.length} style(s) selected</p>
            <Button onClick={handleGenerateSelected} disabled={running || selected.length === 0} className="rounded-full font-semibold" data-testid="generate-images-btn">
              {running ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Wand2 className="mr-1 h-4 w-4" />}
              Generate {selected.length > 0 ? `(${selected.length})` : ""}
            </Button>
          </div>
        </div>
      </div>

      {/* Generated gallery */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="font-heading font-bold text-sm">Generated images ({generated.length})</p>
          {generated.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleZip} className="rounded-full" data-testid="download-zip-btn">
              <FileArchive className="mr-1 h-4 w-4" /> Download ZIP
            </Button>
          )}
        </div>
        {generated.length === 0 ? (
          <p className="text-muted-foreground text-center py-8 text-sm">No images generated yet. Select styles above and generate.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {generated.map((img) => (
              <motion.div key={img.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="group relative rounded-xl overflow-hidden border border-border" data-testid={`generated-image-${img.id}`}>
                <img src={img.data} alt={img.label} className="w-full aspect-square object-cover" />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                  <p className="text-white text-xs font-medium truncate">{img.label}</p>
                </div>
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => downloadDataUrl(img.data, `${img.label}.png`)} className="h-7 w-7 rounded-full bg-black/60 text-white flex items-center justify-center" data-testid={`download-image-${img.id}`}>
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  <button onClick={() => handleDelete(img.id)} className="h-7 w-7 rounded-full bg-black/60 text-white flex items-center justify-center" data-testid={`delete-image-${img.id}`}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
