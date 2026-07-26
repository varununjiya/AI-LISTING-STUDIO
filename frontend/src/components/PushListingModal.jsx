import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { MarketplaceIcon } from "@/components/MarketplaceIcons";
import { toast } from "sonner";
import api from "@/lib/api";
import { Upload, Sparkles, Loader2, CheckCircle2, Image as ImageIcon, Plus } from "lucide-react";

export default function PushListingModal({ isOpen, onClose, marketplace, product, onSuccess }) {
  const [selectedImages, setSelectedImages] = useState([]);
  const [availableImages, setAvailableImages] = useState([]);
  const [publishing, setPublishing] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (product) {
      const uploaded = (product.images || []).map((img, idx) => ({
        id: `up_${idx}`,
        url: img,
        label: `Uploaded ${idx + 1}`,
      }));
      const generated = (product.generated_images || []).map((img, idx) => ({
        id: `gen_${idx}`,
        url: img.data || img,
        label: img.label || `AI Scene ${idx + 1}`,
      }));
      const all = [...uploaded, ...generated];
      setAvailableImages(all);
      // Select all by default
      setSelectedImages(all.map((item) => item.url));
    }
  }, [product]);

  const toggleSelectImage = (url) => {
    setSelectedImages((prev) =>
      prev.includes(url) ? prev.filter((item) => item !== url) : [...prev, url]
    );
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setUploading(true);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Url = reader.result;
        const newImg = {
          id: `new_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
          url: base64Url,
          label: file.name,
        };
        setAvailableImages((prev) => [...prev, newImg]);
        setSelectedImages((prev) => [...prev, base64Url]);
        setUploading(false);
        toast.success(`Uploaded ${file.name}`);
      };
      reader.readAsDataURL(file);
    });
  };

  const handlePublish = async () => {
    if (!marketplace) return;
    if (selectedImages.length === 0) {
      toast.error("Please select at least one image to push to the marketplace.");
      return;
    }

    setPublishing(true);
    try {
      const { data } = await api.post("/marketplaces/publish", {
        product_id: product.id,
        marketplace: marketplace.toLowerCase(),
        sku: product.sku,
        selected_images: selectedImages,
      });

      if (data.success) {
        toast.success(data.message || `Successfully pushed listing to ${marketplace.toUpperCase()}!`);
        if (onSuccess) onSuccess(data);
        onClose();
      } else {
        toast.error(data.error || `Failed to push listing to ${marketplace.toUpperCase()}`);
      }
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Push listing failed");
    } finally {
      setPublishing(false);
    }
  };

  if (!product || !marketplace) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 text-slate-100 border-slate-800 p-6 space-y-5 rounded-2xl shadow-2xl">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
              <MarketplaceIcon marketplace={marketplace.toLowerCase()} className="w-7 h-7" />
            </div>
            <div>
              <DialogTitle className="text-xl font-bold text-slate-100">
                Push Listing to {marketplace.toUpperCase()}
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                Select which images to attach to your seller catalog and optionally upload new product photos before pushing.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Image Selection Grid */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <ImageIcon className="w-4 h-4 text-indigo-400" /> Select Product Images ({selectedImages.length} selected)
            </label>

            {/* Direct Upload Button */}
            <label className="cursor-pointer inline-flex items-center gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg font-medium transition-colors shadow-sm">
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              Upload New Image
              <input type="file" accept="image/*" multiple onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          {availableImages.length === 0 ? (
            <div className="py-8 text-center bg-slate-950/60 rounded-xl border border-slate-800 text-slate-400 text-xs">
              No images available yet. Upload one above or generate AI studio scenes.
            </div>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 max-h-64 overflow-y-auto p-1 custom-scrollbar">
              {availableImages.map((img, idx) => {
                const isSelected = selectedImages.includes(img.url);
                return (
                  <div
                    key={img.id || idx}
                    onClick={() => toggleSelectImage(img.url)}
                    className={`relative group rounded-xl overflow-hidden border cursor-pointer transition-all duration-200 aspect-square ${
                      isSelected
                        ? "border-indigo-500 ring-2 ring-indigo-500/50 bg-indigo-500/10"
                        : "border-slate-800 bg-slate-950 opacity-60 hover:opacity-100"
                    }`}
                  >
                    <img src={img.url} alt={img.label} className="w-full h-full object-cover" />
                    
                    {/* Checkbox overlay */}
                    <div className="absolute top-1.5 left-1.5 bg-slate-950/80 p-1 rounded-md">
                      <Checkbox checked={isSelected} onCheckedChange={() => toggleSelectImage(img.url)} />
                    </div>

                    {/* Label Badge */}
                    <div className="absolute bottom-1 right-1 left-1 bg-slate-950/80 backdrop-blur-sm px-1.5 py-0.5 rounded text-[10px] text-slate-300 truncate">
                      {idx === 0 ? "Main Image" : img.label}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Product Details Summary */}
        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs space-y-1">
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Target Product:</span>
            <span className="font-semibold text-slate-100">{product.product_name}</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">SKU:</span>
            <span className="font-mono text-slate-200">{product.sku || `SKU-${product.id.slice(0, 8)}`}</span>
          </div>
        </div>

        <DialogFooter className="flex gap-2 justify-end">
          <Button variant="outline" onClick={onClose} disabled={publishing} className="border-slate-800 bg-slate-850 hover:bg-slate-800 text-slate-300">
            Cancel
          </Button>
          <Button onClick={handlePublish} disabled={publishing || selectedImages.length === 0} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-2">
            {publishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-amber-300" />}
            Push to {marketplace.toUpperCase()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
