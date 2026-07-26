import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Save, Loader2, Cpu, KeyRound, CheckCircle2, AlertTriangle, Sparkles, CreditCard, ShieldCheck, Trash2, ExternalLink, Zap, Layers, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Breadcrumbs from "@/components/Breadcrumbs";
import { MarketplaceIcon } from "@/components/MarketplaceIcons";
import ConnectMarketplaceModal from "@/components/ConnectMarketplaceModal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DEFAULTS = {
  ai_provider: "gemini",
  image_service: "gemini",
  api_key: "",
  use_own_key: false,
  text_model: "",
  image_model: "gemini-3.1-flash-image-preview",
  default_marketplace: "amazon",
  brand_tone: "professional",
  language: "English",
  title_char_limit: 200,
  description_char_limit: 2000,
  default_export_format: "generic",
};

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

export default function Settings() {
  const [form, setForm] = useState(DEFAULTS);
  const [meta, setMeta] = useState({ ai_configured: false, emergent_key_available: false, api_key_set: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Marketplaces state
  const [marketplaces, setMarketplaces] = useState(null);
  const [connectModalMp, setConnectModalMp] = useState(null);

  // Subscription state
  const [subData, setSubData] = useState(null);
  const [upgradingPlan, setUpgradingPlan] = useState(null);

  const loadMarketplaces = async () => {
    try {
      const res = await api.get("/marketplaces/dashboard");
      setMarketplaces(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSubscription = async () => {
    try {
      const res = await api.get("/subscriptions/my-subscription");
      setSubData(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    Promise.all([
      api.get("/settings"),
      loadMarketplaces(),
      loadSubscription(),
    ]).then(([{ data }]) => {
      setForm({ ...DEFAULTS, ...data, api_key: "" });
      setMeta({
        ai_configured: data.ai_configured,
        emergent_key_available: data.emergent_key_available,
        api_key_set: !!data.api_key_set,
      });
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        title_char_limit: parseInt(form.title_char_limit, 10) || 200,
        description_char_limit: parseInt(form.description_char_limit, 10) || 2000,
      };
      const { data } = await api.put("/settings", payload);
      setMeta({
        ai_configured: data.ai_configured,
        emergent_key_available: data.emergent_key_available,
        api_key_set: !!data.api_key_set,
      });
      setForm((f) => ({ ...f, api_key: "" }));
      toast.success("Settings saved successfully");
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async (mp) => {
    if (!window.confirm(`Are you sure you want to disconnect ${mp.toUpperCase()}?`)) return;
    try {
      await api.delete(`/marketplaces/${mp}/disconnect`);
      toast.success(`${mp.toUpperCase()} disconnected`);
      loadMarketplaces();
    } catch (err) {
      toast.error("Failed to disconnect marketplace");
    }
  };

  const handleUpgrade = async (planId) => {
    setUpgradingPlan(planId);
    try {
      const isScriptLoaded = await loadRazorpayScript();
      if (!isScriptLoaded) {
        toast.error("Failed to load Razorpay SDK. Please check your internet connection.");
        setUpgradingPlan(null);
        return;
      }

      const { data: order } = await api.post("/subscriptions/create-order", { plan_id: planId });

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "AI Listing Studio",
        description: `${order.plan_name} Upgrade`,
        order_id: order.order_id,
        handler: async (response) => {
          try {
            await api.post("/subscriptions/verify", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            toast.success(`Upgraded to ${order.plan_name} successfully!`);
            loadSubscription();
          } catch (err) {
            toast.error("Payment verification failed");
          }
        },
        prefill: {},
        theme: {
          color: "#4F46E5",
        },
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.open();
    } catch (err) {
      console.error(err);
      toast.error("Failed to initiate subscription order");
    } finally {
      setUpgradingPlan(null);
    }
  };

  const handleCancelSub = async () => {
    if (!window.confirm("Are you sure you want to cancel your Pro subscription? You will be reverted to the Free plan.")) return;
    try {
      await api.post("/subscriptions/cancel");
      toast.success("Subscription cancelled");
      loadSubscription();
    } catch (err) {
      toast.error("Failed to cancel subscription");
    }
  };

  if (loading) return <div className="h-64 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>;

  return (
    <div className="space-y-8 max-w-4xl pb-12" data-testid="settings-page">
      <Breadcrumbs items={[{ label: "Dashboard", to: "/dashboard" }, { label: "Settings" }]} />
      
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Configuration & SaaS Management</p>
        <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Settings & Marketplace Connections</h1>
        <p className="text-slate-400 text-sm mt-1">Manage Amazon, Flipkart & Meesho seller accounts, AI providers, and subscription billing.</p>
      </div>

      {/* ---------------- Marketplace Connections Section ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <Layers className="h-5 w-5 text-indigo-400" />
            <h2 className="font-heading font-bold text-lg text-slate-100">Marketplace Accounts</h2>
          </div>
          <p className="text-xs text-slate-400">Connect seller accounts to import catalog items</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { id: "amazon", name: "Amazon SP-API" },
            { id: "flipkart", name: "Flipkart Seller API" },
            { id: "meesho", name: "Meesho Seller API" },
          ].map((mp) => {
            const mpConn = marketplaces?.[mp.id] || { connected: false };
            return (
              <div key={mp.id} className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      <MarketplaceIcon marketplace={mp.id} className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-100 text-sm">{mp.name}</h4>
                      <Badge
                        variant="outline"
                        className={`text-[10px] px-2 py-0.5 rounded-full ${
                          mpConn.connected ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {mpConn.connected ? "Connected" : "Disconnected"}
                      </Badge>
                    </div>
                  </div>
                </div>

                {mpConn.connected ? (
                  <div className="space-y-2">
                    <div className="text-xs text-slate-400 truncate">
                      Listings: <span className="text-slate-200 font-semibold">{mpConn.total_listings}</span> | Orders: <span className="text-slate-200 font-semibold">{mpConn.total_orders}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setConnectModalMp(mp.id)}
                        className="flex-1 text-xs border-slate-700 bg-slate-850 hover:bg-slate-800 text-slate-200"
                      >
                        Configure
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDisconnect(mp.id)}
                        className="text-rose-400 hover:bg-rose-500/10 text-xs px-2.5"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => setConnectModalMp(mp.id)}
                    className="w-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    Connect Account
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ---------------- Subscriptions & Billing Section ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <CreditCard className="h-5 w-5 text-indigo-400" />
            <h2 className="font-heading font-bold text-lg text-slate-100">Subscription & Usage Limits</h2>
          </div>
          <Badge className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 uppercase text-xs">
            {subData?.plan_name || "Free Plan"}
          </Badge>
        </div>

        {/* Current Usage Progress */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-3">
          <div className="flex justify-between text-xs text-slate-300">
            <span className="flex items-center gap-1.5 font-medium">
              <Zap className="w-4 h-4 text-amber-400" /> AI Generation Usage
            </span>
            <span>
              {subData?.usage_count ?? 0} / {subData?.is_unlimited ? "Unlimited" : subData?.limit ?? 1} Generations Used
            </span>
          </div>

          {!subData?.is_unlimited && (
            <Progress value={Math.min(100, (((subData?.usage_count || 0) / (subData?.limit || 1)) * 100))} className="h-2 bg-slate-800" />
          )}
        </div>

        {/* Plan Upgrade Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Monthly Pro */}
          <div className={`p-5 rounded-xl border flex flex-col justify-between space-y-4 ${
            subData?.plan_id === "monthly_pro" ? "border-indigo-500 bg-indigo-500/5 ring-1 ring-indigo-500" : "border-slate-800 bg-slate-950/60"
          }`}>
            <div>
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-slate-100 text-lg">Monthly Pro</h4>
                <div className="text-xl font-extrabold text-indigo-400">₹100<span className="text-xs font-normal text-slate-400">/mo</span></div>
              </div>
              <ul className="text-xs text-slate-300 space-y-2 mt-3">
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Unlimited AI Generations</li>
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Priority Processing Queue</li>
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Amazon, Flipkart & Meesho Sync</li>
              </ul>
            </div>

            {subData?.plan_id === "monthly_pro" ? (
              <Button variant="outline" disabled className="w-full text-xs border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
                Active Plan
              </Button>
            ) : (
              <Button
                onClick={() => handleUpgrade("monthly_pro")}
                disabled={upgradingPlan === "monthly_pro"}
                className="w-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                {upgradingPlan === "monthly_pro" ? "Processing..." : "Upgrade to Monthly Pro (₹100)"}
              </Button>
            )}
          </div>

          {/* Yearly Pro */}
          <div className={`p-5 rounded-xl border flex flex-col justify-between space-y-4 ${
            subData?.plan_id === "yearly_pro" ? "border-purple-500 bg-purple-500/5 ring-1 ring-purple-500" : "border-slate-800 bg-slate-950/60"
          }`}>
            <div>
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-slate-100 text-lg flex items-center gap-1.5">
                  Yearly Pro <Sparkles className="w-4 h-4 text-amber-300" />
                </h4>
                <div className="text-xl font-extrabold text-purple-400">₹1000<span className="text-xs font-normal text-slate-400">/yr</span></div>
              </div>
              <ul className="text-xs text-slate-300 space-y-2 mt-3">
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Unlimited AI Generations</li>
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Priority Processing Queue</li>
                <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> Advanced Dashboard Analytics</li>
              </ul>
            </div>

            {subData?.plan_id === "yearly_pro" ? (
              <Button variant="outline" disabled className="w-full text-xs border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
                Active Plan
              </Button>
            ) : (
              <Button
                onClick={() => handleUpgrade("yearly_pro")}
                disabled={upgradingPlan === "yearly_pro"}
                className="w-full text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
              >
                {upgradingPlan === "yearly_pro" ? "Processing..." : "Upgrade to Yearly Pro (₹1000)"}
              </Button>
            )}
          </div>
        </div>

        {subData?.plan_id !== "free" && (
          <div className="flex justify-end pt-2">
            <Button variant="ghost" onClick={handleCancelSub} className="text-xs text-rose-400 hover:bg-rose-500/10">
              Cancel Subscription
            </Button>
          </div>
        )}
      </div>

      {/* ---------------- AI Engine & Image Generation Provider Section ---------------- */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-4">
          <Cpu className="h-5 w-5 text-indigo-400" />
          <h2 className="font-heading font-bold text-lg text-slate-100">AI & Image Generation Engine</h2>
        </div>

        <div className="grid sm:grid-cols-2 gap-5">
          <div className="space-y-2">
            <Label className="text-xs text-slate-300">Image Generation Provider (.env IMAGE_GENERATION_PROVIDER)</Label>
            <Select value={form.image_service || "gemini"} onValueChange={(v) => set("image_service", v)}>
              <SelectTrigger className="rounded-xl bg-slate-950 border-slate-800 text-slate-100">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                <SelectItem value="gemini">Google Gemini (Imagen 3)</SelectItem>
                <SelectItem value="huggingface">HuggingFace (FLUX.1 / SD)</SelectItem>
                <SelectItem value="pollinations">Pollinations AI (Fast)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-slate-300">Default Brand Tone</Label>
            <Select value={form.brand_tone || "professional"} onValueChange={(v) => set("brand_tone", v)}>
              <SelectTrigger className="rounded-xl bg-slate-950 border-slate-800 text-slate-100">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                <SelectItem value="professional">Professional & Premium</SelectItem>
                <SelectItem value="engaging">Engaging & Casual</SelectItem>
                <SelectItem value="luxury">Luxury & High-End</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={handleSave} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center gap-2">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Settings
          </Button>
        </div>
      </div>

      {/* Connect Modal */}
      <ConnectMarketplaceModal
        isOpen={!!connectModalMp}
        onClose={() => setConnectModalMp(null)}
        marketplace={connectModalMp}
        onSuccess={loadMarketplaces}
      />
    </div>
  );
}
