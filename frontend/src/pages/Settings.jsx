import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Save, Loader2, Cpu, KeyRound, CheckCircle2, AlertTriangle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import Breadcrumbs from "@/components/Breadcrumbs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DEFAULTS = {
  ai_provider: "gemini",
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

const SelectField = ({ label, value, onChange, options, testid }) => (
  <div className="space-y-2">
    <Label>{label}</Label>
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="rounded-xl" data-testid={testid}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  </div>
);

export default function Settings() {
  const [form, setForm] = useState(DEFAULTS);
  const [meta, setMeta] = useState({ ai_configured: false, emergent_key_available: false, api_key_set: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/settings").then(({ data }) => {
      setForm({ ...DEFAULTS, ...data, api_key: "" });
      setMeta({
        ai_configured: data.ai_configured,
        emergent_key_available: data.emergent_key_available,
        api_key_set: !!data.api_key_set,
      });
      setLoading(false);
    });
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
      toast.success("Settings saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="h-64" />;

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
      <Breadcrumbs items={[{ label: "Dashboard", to: "/dashboard" }, { label: "Settings" }]} />
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Configuration</p>
        <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">Configure AI engine, keys and export defaults.</p>
      </div>

      {/* AI status banner */}
      <div
        className={`rounded-2xl border p-4 flex items-start gap-3 ${
          meta.ai_configured ? "border-accent/40 bg-accent/5" : "border-destructive/40 bg-destructive/5"
        }`}
        data-testid="ai-status-banner"
      >
        {meta.ai_configured ? (
          <CheckCircle2 className="h-5 w-5 text-accent shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
        )}
        <div className="text-sm">
          <p className="font-semibold">
            {meta.ai_configured ? "AI is ready" : "AI not configured"}
          </p>
          <p className="text-muted-foreground">
            {form.use_own_key
              ? meta.api_key_set
                ? `Using your own ${form.ai_provider} API key.`
                : "Enter your API key below to use your own provider."
              : meta.emergent_key_available
              ? "Using the Emergent Universal Key. Image generation may need balance — top up under Profile → Universal Key → Add Balance."
              : "No Emergent key detected. Add your own key below."}
          </p>
        </div>
      </div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-border bg-card p-6 sm:p-8 space-y-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="h-4 w-4 text-accent" />
            <h2 className="font-heading font-bold">AI Engine</h2>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-border p-4 mb-5">
            <div>
              <p className="font-medium text-sm">Use my own API key</p>
              <p className="text-xs text-muted-foreground">Off = Emergent Universal Key. On = your own provider key.</p>
            </div>
            <Switch checked={form.use_own_key} onCheckedChange={(v) => set("use_own_key", v)} data-testid="setting-use-own-key" />
          </div>

          <div className="grid sm:grid-cols-2 gap-5">
            <SelectField
              label="AI Provider"
              value={form.ai_provider}
              onChange={(v) => set("ai_provider", v)}
              testid="setting-ai-provider"
              options={[
                { value: "gemini", label: "Google Gemini" },
                { value: "openai", label: "OpenAI" },
                { value: "anthropic", label: "Anthropic Claude" },
              ]}
            />
            <div className="space-y-2">
              <Label className="flex items-center gap-1"><KeyRound className="h-3.5 w-3.5" /> API Key {meta.api_key_set && "(saved)"}</Label>
              <Input
                type="password"
                value={form.api_key}
                onChange={(e) => set("api_key", e.target.value)}
                placeholder={meta.api_key_set ? "•••••••• (leave blank to keep)" : `Your ${form.ai_provider} key`}
                className="rounded-xl"
                disabled={!form.use_own_key}
                data-testid="setting-api-key"
              />
            </div>
            <div className="space-y-2">
              <Label>Text Model (optional override)</Label>
              <Input
                value={form.text_model}
                onChange={(e) => set("text_model", e.target.value)}
                placeholder="Default per provider"
                className="rounded-xl"
                data-testid="setting-text-model"
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-1"><Sparkles className="h-3.5 w-3.5" /> Image Model</Label>
              <Input value={form.image_model} readOnly className="rounded-xl opacity-70" data-testid="setting-image-model" />
            </div>
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h2 className="font-heading font-bold mb-4">Generation Preferences</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            <SelectField label="Default Marketplace" value={form.default_marketplace} onChange={(v) => set("default_marketplace", v)} testid="setting-marketplace"
              options={[{ value: "amazon", label: "Amazon" }, { value: "flipkart", label: "Flipkart" }, { value: "meesho", label: "Meesho" }, { value: "both", label: "All" }]} />
            <SelectField label="Brand Tone" value={form.brand_tone} onChange={(v) => set("brand_tone", v)} testid="setting-tone"
              options={[{ value: "professional", label: "Professional" }, { value: "friendly", label: "Friendly" }, { value: "luxury", label: "Luxury" }, { value: "playful", label: "Playful" }]} />
            <SelectField label="Language" value={form.language} onChange={(v) => set("language", v)} testid="setting-language"
              options={[{ value: "English", label: "English" }, { value: "Hindi", label: "Hindi" }, { value: "Spanish", label: "Spanish" }, { value: "French", label: "French" }]} />
            <SelectField label="Default Export Format" value={form.default_export_format} onChange={(v) => set("default_export_format", v)} testid="setting-export-format"
              options={[{ value: "generic", label: "Generic Excel" }, { value: "amazon", label: "Amazon Excel" }, { value: "flipkart", label: "Flipkart Excel" }, { value: "meesho", label: "Meesho Excel" }]} />
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h2 className="font-heading font-bold mb-4">Character Limits</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            <div className="space-y-2">
              <Label>Title Character Limit</Label>
              <Input type="number" value={form.title_char_limit} onChange={(e) => set("title_char_limit", e.target.value)} className="rounded-xl" data-testid="setting-title-limit" />
            </div>
            <div className="space-y-2">
              <Label>Description Character Limit</Label>
              <Input type="number" value={form.description_char_limit} onChange={(e) => set("description_char_limit", e.target.value)} className="rounded-xl" data-testid="setting-desc-limit" />
            </div>
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <Button onClick={handleSave} disabled={saving} className="rounded-full font-semibold" data-testid="save-settings-btn">
            {saving ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Save className="mr-1 h-4 w-4" />}
            Save Settings
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
