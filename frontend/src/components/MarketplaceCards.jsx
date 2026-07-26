import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MarketplaceIcon } from "@/components/MarketplaceIcons";
import { CheckCircle2, XCircle, Plus, RefreshCw, ShoppingCart, Package, IndianRupee, Layers } from "lucide-react";

export default function MarketplaceCards({ data, onConnect, onRefresh }) {
  const marketplaces = [
    { id: "amazon", name: "Amazon SP-API", badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
    { id: "flipkart", name: "Flipkart Seller API", badgeBg: "bg-blue-500/10 text-blue-400 border-blue-500/30" },
    { id: "meesho", name: "Meesho Seller API", badgeBg: "bg-pink-500/10 text-pink-400 border-pink-500/30" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {marketplaces.map((mp) => {
        const mpData = data?.[mp.id] || { connected: false };
        const isConnected = mpData.connected;

        return (
          <Card key={mp.id} className="bg-slate-900 border-slate-800 text-slate-100 relative overflow-hidden group hover:border-slate-700 transition-all duration-300 shadow-xl">
            {/* Top Accent Line */}
            <div
              className={`h-1 w-full ${
                mp.id === "amazon" ? "bg-amber-500" : mp.id === "flipkart" ? "bg-blue-500" : "bg-pink-500"
              }`}
            />

            <CardContent className="p-5 space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 shadow-inner">
                    <MarketplaceIcon marketplace={mp.id} className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-base">{mp.name}</h3>
                    <p className="text-slate-400 text-xs">
                      {isConnected ? `ID: ${mpData.seller_id || "Connected"}` : "Not connected"}
                    </p>
                  </div>
                </div>

                <Badge
                  variant="outline"
                  className={`text-xs px-2.5 py-0.5 rounded-full flex items-center gap-1 font-medium ${
                    isConnected
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                      : "bg-slate-800 text-slate-400 border-slate-700"
                  }`}
                >
                  {isConnected ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Connected
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3 h-3 text-slate-400" /> Disconnected
                    </>
                  )}
                </Badge>
              </div>

              {/* Metrics Grid */}
              {isConnected ? (
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Layers className="w-3.5 h-3.5 text-indigo-400" /> Total Listings
                    </div>
                    <div className="text-lg font-bold text-slate-100 mt-1">{mpData.total_listings}</div>
                  </div>

                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <ShoppingCart className="w-3.5 h-3.5 text-emerald-400" /> Orders
                    </div>
                    <div className="text-lg font-bold text-slate-100 mt-1">{mpData.total_orders}</div>
                  </div>

                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Package className="w-3.5 h-3.5 text-purple-400" /> Inventory
                    </div>
                    <div className="text-lg font-bold text-slate-100 mt-1">{mpData.total_inventory}</div>
                  </div>

                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <IndianRupee className="w-3.5 h-3.5 text-amber-400" /> Revenue
                    </div>
                    <div className="text-lg font-bold text-amber-300 mt-1">₹{mpData.total_revenue.toLocaleString("en-IN")}</div>
                  </div>
                </div>
              ) : (
                <div className="py-6 text-center text-slate-500 bg-slate-950/30 rounded-lg border border-slate-800/50">
                  <p className="text-xs">Connect your account to sync catalog, inventory, & orders.</p>
                </div>
              )}

              {/* Action Button */}
              <div className="pt-1">
                {isConnected ? (
                  <Button
                    variant="outline"
                    onClick={() => onConnect(mp.id)}
                    className="w-full text-xs border-slate-800 bg-slate-850 hover:bg-slate-800 text-slate-300"
                  >
                    Manage Connection
                  </Button>
                ) : (
                  <Button
                    onClick={() => onConnect(mp.id)}
                    className="w-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center gap-1.5 shadow-md shadow-indigo-500/20"
                  >
                    <Plus className="w-4 h-4" /> Connect Account
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
