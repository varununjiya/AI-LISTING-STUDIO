import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { MarketplaceIcon } from "@/components/MarketplaceIcons";
import { toast } from "sonner";
import api from "@/lib/api";
import { Download, RefreshCw, CheckCircle2, ArrowRight, Package, Loader2, Sparkles } from "lucide-react";

export default function ImportProducts() {
  const navigate = useNavigate();
  const [selectedMarketplace, setSelectedMarketplace] = useState("amazon");
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [fetchedItems, setFetchedItems] = useState([]);
  const [selectedSKUs, setSelectedSKUs] = useState([]);

  const fetchProducts = async (mp = selectedMarketplace) => {
    setLoading(true);
    setFetchedItems([]);
    setSelectedSKUs([]);
    try {
      const res = await api.get(`/marketplaces/${mp}/products`);
      setFetchedItems(res.data || []);
      // Auto-select all items by default
      if (res.data && res.data.length > 0) {
        setSelectedSKUs(res.data.map((item) => item.sku || item.asin || item.fsn || item.meesho_id));
      }
      toast.success(`Fetched ${res.data.length} products from ${mp.toUpperCase()}`);
    } catch (err) {
      console.error(err);
      toast.error(`Failed to fetch products from ${mp}. Please check account connection.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(selectedMarketplace);
  }, [selectedMarketplace]);

  const toggleSelectAll = () => {
    if (selectedSKUs.length === fetchedItems.length) {
      setSelectedSKUs([]);
    } else {
      setSelectedSKUs(fetchedItems.map((item) => item.sku || item.asin || item.fsn || item.meesho_id));
    }
  };

  const toggleSelectSKU = (sku) => {
    setSelectedSKUs((prev) =>
      prev.includes(sku) ? prev.filter((id) => id !== sku) : [...prev, sku]
    );
  };

  const handleImport = async () => {
    if (selectedSKUs.length === 0) {
      toast.error("Please select at least one product to import.");
      return;
    }

    const itemsToImport = fetchedItems.filter((item) =>
      selectedSKUs.includes(item.sku || item.asin || item.fsn || item.meesho_id)
    );

    setImporting(true);
    try {
      const res = await api.post("/marketplaces/import", {
        marketplace: selectedMarketplace,
        items: itemsToImport,
      });

      toast.success(`Successfully imported ${res.data.imported_count} products into AI Listing Studio!`);
      navigate("/products");
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Import failed");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Download className="w-6 h-6 text-indigo-400" /> Import Marketplace Products
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Fetch catalog items directly from Amazon, Flipkart, or Meesho into AI Listing Studio for one-click AI generation.
          </p>
        </div>

        <Button
          onClick={handleImport}
          disabled={importing || selectedSKUs.length === 0}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium shadow-lg shadow-indigo-500/25 flex items-center gap-2"
        >
          {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-amber-300" />}
          Import Selected ({selectedSKUs.length})
        </Button>
      </div>

      {/* Marketplace Selector Tabs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { id: "amazon", name: "Amazon SP-API", color: "from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-300" },
          { id: "flipkart", name: "Flipkart Seller Hub", color: "from-blue-500/20 to-cyan-500/10 border-blue-500/40 text-blue-300" },
          { id: "meesho", name: "Meesho Supplier API", color: "from-pink-500/20 to-rose-500/10 border-pink-500/40 text-pink-300" },
        ].map((mp) => (
          <button
            key={mp.id}
            onClick={() => setSelectedMarketplace(mp.id)}
            className={`p-4 rounded-xl border text-left transition-all duration-200 flex items-center justify-between ${
              selectedMarketplace === mp.id
                ? `bg-gradient-to-r ${mp.color} ring-2 ring-indigo-500`
                : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:bg-slate-850"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                <MarketplaceIcon marketplace={mp.id} className="w-7 h-7" />
              </div>
              <div>
                <div className="font-semibold text-slate-100 text-base">{mp.name}</div>
                <div className="text-xs text-slate-400">Click to fetch catalog</div>
              </div>
            </div>

            {selectedMarketplace === mp.id && <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0" />}
          </button>
        ))}
      </div>

      {/* Products Table Card */}
      <Card className="bg-slate-900 border-slate-800 text-slate-100">
        <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Package className="w-5 h-5 text-indigo-400" />
              Available Products ({fetchedItems.length})
            </CardTitle>
            <CardDescription className="text-slate-400 text-xs mt-0.5">
              Select products to auto-populate Title, Description, Brand, Images, Price, SKU, and Specifications.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchProducts(selectedMarketplace)}
            disabled={loading}
            className="border-slate-700 bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </CardHeader>

        <CardContent className="p-0">
          {loading ? (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              <p className="text-sm">Fetching catalog products from {selectedMarketplace.toUpperCase()}...</p>
            </div>
          ) : fetchedItems.length === 0 ? (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
              <Package className="w-12 h-12 text-slate-600 mb-1" />
              <p className="text-slate-300 font-medium">No products found in this marketplace account</p>
              <p className="text-xs text-slate-500 max-w-sm">
                Connect your {selectedMarketplace.toUpperCase()} Seller account in Settings or refresh the list.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 text-xs uppercase font-semibold">
                    <th className="p-4 w-12">
                      <Checkbox
                        checked={selectedSKUs.length === fetchedItems.length && fetchedItems.length > 0}
                        onCheckedChange={toggleSelectAll}
                      />
                    </th>
                    <th className="p-4">Product Info</th>
                    <th className="p-4">SKU / ID</th>
                    <th className="p-4">Brand</th>
                    <th className="p-4">Category</th>
                    <th className="p-4 text-right">Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {fetchedItems.map((item) => {
                    const itemKey = item.sku || item.asin || item.fsn || item.meesho_id;
                    const isSelected = selectedSKUs.includes(itemKey);
                    const imageSrc = (item.images && item.images[0]) || null;

                    return (
                      <tr
                        key={itemKey}
                        className={`hover:bg-slate-800/40 transition-colors cursor-pointer ${
                          isSelected ? "bg-indigo-500/5" : ""
                        }`}
                        onClick={() => toggleSelectSKU(itemKey)}
                      >
                        <td className="p-4" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleSelectSKU(itemKey)}
                          />
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            {imageSrc ? (
                              <img
                                src={imageSrc}
                                alt={item.product_name}
                                className="w-10 h-10 object-cover rounded-lg border border-slate-700 bg-slate-950"
                              />
                            ) : (
                              <div className="w-10 h-10 rounded-lg border border-slate-800 bg-slate-950 flex items-center justify-center text-slate-600 text-xs">
                                No Img
                              </div>
                            )}
                            <div>
                              <div className="font-medium text-slate-100 line-clamp-1">{item.product_name}</div>
                              <div className="text-xs text-slate-400 line-clamp-1">{item.description}</div>
                            </div>
                          </div>
                        </td>
                        <td className="p-4 font-mono text-xs text-indigo-300">{itemKey}</td>
                        <td className="p-4 text-xs">{item.brand || "Generic"}</td>
                        <td className="p-4">
                          <Badge variant="outline" className="border-slate-700 text-slate-300 text-[11px]">
                            {item.category || item.product_type || "General"}
                          </Badge>
                        </td>
                        <td className="p-4 text-right font-semibold text-slate-100">
                          ₹{item.selling_price || item.mrp || "N/A"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
