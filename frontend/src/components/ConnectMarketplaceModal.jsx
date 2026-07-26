import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MarketplaceIcon } from "@/components/MarketplaceIcons";
import { toast } from "sonner";
import api from "@/lib/api";
import { ExternalLink, Lock, CheckCircle2 } from "lucide-react";

export default function ConnectMarketplaceModal({ isOpen, onClose, marketplace, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    client_id: "",
    client_secret: "",
    refresh_token: "",
    seller_id: "",
    app_id: "",
    app_secret: "",
    api_key: "",
    supplier_id: "",
  });

  if (!marketplace) return null;

  const mpName = marketplace.charAt(0).toUpperCase() + marketplace.slice(1);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post(`/marketplaces/${marketplace}/connect`, formData);
      toast.success(`${mpName} account connected successfully!`);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || `Failed to connect ${mpName} account`);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthRedirect = () => {
    toast.info(`Redirecting to ${mpName} OAuth authorization portal...`);
    let authUrl = "#";
    const redirectUri = encodeURIComponent(`${window.location.origin}/settings`);

    if (marketplace === "amazon") {
      authUrl = `https://sellercentral.amazon.in/apps/authorize/consent?application_id=amzn1.sp.solution.mock-app-id&redirect_uri=${redirectUri}&state=amz_state`;
    } else if (marketplace === "flipkart") {
      authUrl = `https://api.flipkart.net/oauth-service/oauth/authorize?response_type=code&client_id=mock_app_id&redirect_uri=${redirectUri}&state=fk_state`;
    }

    window.open(authUrl, "_blank");
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-slate-100">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-lg bg-slate-800 border border-slate-700">
              <MarketplaceIcon marketplace={marketplace} className="w-8 h-8" />
            </div>
            <div>
              <DialogTitle className="text-xl font-bold">Connect {mpName}</DialogTitle>
              <DialogDescription className="text-slate-400 text-xs">
                Authorize AI Listing Studio to sync listings, orders, & inventory.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="my-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-300 flex items-start gap-2">
          <Lock className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            Credentials are end-to-end encrypted with Fernet AES-256 before storage.
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {marketplace === "amazon" && (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={handleOAuthRedirect}
                className="w-full bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20 flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" /> OAuth Login via Amazon Seller Central
              </Button>
              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-slate-800"></div>
                <span className="flex-shrink mx-2 text-[10px] text-slate-500 uppercase">Or enter credentials manually</span>
                <div className="flex-grow border-t border-slate-800"></div>
              </div>

              <div>
                <Label className="text-xs text-slate-300">Seller ID / Merchant Token</Label>
                <Input
                  placeholder="e.g. A2XXXXXXXXXX"
                  value={formData.seller_id}
                  onChange={(e) => setFormData({ ...formData, seller_id: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">LWA Client ID</Label>
                <Input
                  placeholder="amzn1.application-oa2-client.xxx"
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">LWA Client Secret</Label>
                <Input
                  type="password"
                  placeholder="amzn1.oa2-cs.v1.xxx"
                  value={formData.client_secret}
                  onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">LWA Refresh Token</Label>
                <Input
                  type="password"
                  placeholder="Atzr|IwEBI..."
                  value={formData.refresh_token}
                  onChange={(e) => setFormData({ ...formData, refresh_token: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>
            </>
          )}

          {marketplace === "flipkart" && (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={handleOAuthRedirect}
                className="w-full bg-blue-500/10 text-blue-400 border-blue-500/30 hover:bg-blue-500/20 flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" /> Authorize via Flipkart Seller Hub
              </Button>
              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-slate-800"></div>
                <span className="flex-shrink mx-2 text-[10px] text-slate-500 uppercase">Or enter credentials manually</span>
                <div className="flex-grow border-t border-slate-800"></div>
              </div>

              <div>
                <Label className="text-xs text-slate-300">Application ID</Label>
                <Input
                  placeholder="e.g. fk_app_xxxxxxxx"
                  value={formData.app_id}
                  onChange={(e) => setFormData({ ...formData, app_id: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">Application Secret</Label>
                <Input
                  type="password"
                  placeholder="fk_sec_xxxxxxxx"
                  value={formData.app_secret}
                  onChange={(e) => setFormData({ ...formData, app_secret: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">Refresh Token</Label>
                <Input
                  type="password"
                  placeholder="fk_ref_xxxxxxxx"
                  value={formData.refresh_token}
                  onChange={(e) => setFormData({ ...formData, refresh_token: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>
            </>
          )}

          {marketplace === "meesho" && (
            <>
              <div>
                <Label className="text-xs text-slate-300">Supplier / Vendor ID</Label>
                <Input
                  placeholder="e.g. MSH-SUP-10293"
                  value={formData.supplier_id}
                  onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>

              <div>
                <Label className="text-xs text-slate-300">Meesho API Key / Token</Label>
                <Input
                  type="password"
                  placeholder="meesho_api_key_xxxxxxxx"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="bg-slate-950 border-slate-800 text-slate-100 text-xs mt-1"
                />
              </div>
            </>
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={onClose} className="text-slate-400 hover:text-white">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
            >
              {loading ? "Connecting..." : (
                <>
                  <CheckCircle2 className="w-4 h-4" /> Save & Connect
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
