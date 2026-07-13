import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileSpreadsheet, Sparkles, Loader2, FileText, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function BulkUpload() {
  const [uploads, setUploads] = useState([]);
  const [active, setActive] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const loadUploads = async () => {
    try {
      const { data } = await api.get("/uploads");
      setUploads(data);
      if (data.length && !active) setActive(data[0]);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadUploads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFile = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/uploads", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`Uploaded ${data.filename} — ${data.row_count} rows parsed`);
      setActive(data);
      loadUploads();
    } catch {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateAll = async (upload) => {
    setGeneratingId(upload.id);
    try {
      const { data } = await api.post(`/uploads/${upload.id}/generate-all`);
      toast.success(`Generated ${data.created} listings`);
      loadUploads();
    } catch {
      toast.error("Bulk generation failed");
    } finally {
      setGeneratingId(null);
    }
  };

  const columns = active?.rows?.length
    ? Array.from(new Set(active.rows.flatMap((r) => Object.keys(r)))).slice(0, 6)
    : [];

  return (
    <div className="space-y-8" data-testid="bulk-upload-page">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Batch processing</p>
        <h1 className="font-heading font-black text-3xl sm:text-4xl tracking-tight">Bulk Upload</h1>
        <p className="text-muted-foreground mt-2">Upload Excel, CSV or PDF and generate listings for every product at once.</p>
      </div>

      {/* Dropzone */}
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        data-testid="dropzone"
        className={`block rounded-3xl border-2 border-dashed p-12 text-center cursor-pointer transition-colors ${
          dragOver ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
        }`}
      >
        <input
          type="file"
          accept=".xlsx,.xls,.csv,.pdf"
          className="hidden"
          data-testid="bulk-file-input"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <div className="h-14 w-14 rounded-2xl bg-secondary flex items-center justify-center mx-auto mb-4">
          {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <UploadCloud className="h-6 w-6" />}
        </div>
        <p className="font-heading font-bold">Drop a file here or click to upload</p>
        <p className="text-sm text-muted-foreground mt-1">Supports .xlsx, .csv and .pdf</p>
      </label>

      {/* Parsed preview */}
      {active && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-border bg-card">
          <div className="flex flex-wrap items-center justify-between gap-3 p-5 border-b border-border">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="font-heading font-bold">{active.filename}</span>
              <Badge variant="secondary" className="rounded-full">{active.row_count} rows</Badge>
              {active.status === "generated" && (
                <Badge className="rounded-full bg-accent text-accent-foreground border-0">Generated</Badge>
              )}
            </div>
            <Button
              onClick={() => handleGenerateAll(active)}
              disabled={generatingId === active.id || !active.row_count}
              className="rounded-full font-semibold"
              data-testid="generate-all-btn"
            >
              {generatingId === active.id ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
              Generate Listings for All
            </Button>
          </div>
          {active.rows?.length ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {columns.map((c) => (
                      <TableHead key={c} className="capitalize">{c.replace(/_/g, " ")}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {active.rows.slice(0, 20).map((r, i) => (
                    <TableRow key={i} data-testid={`upload-row-${i}`}>
                      {columns.map((c) => (
                        <TableCell key={c} className="max-w-[200px] truncate">{r[c] || "—"}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="p-8 text-center text-muted-foreground">No rows parsed from this file.</p>
          )}
        </motion.div>
      )}

      {/* Past uploads */}
      {uploads.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-5">
          <h2 className="font-heading font-bold text-lg mb-4">Upload history</h2>
          <div className="space-y-2">
            {uploads.map((u) => (
              <button
                key={u.id}
                onClick={() => setActive(u)}
                data-testid={`upload-history-${u.id}`}
                className="w-full flex items-center justify-between rounded-xl border border-border px-4 py-3 hover:bg-secondary transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{u.filename}</span>
                  <span className="text-xs text-muted-foreground">{u.row_count} rows</span>
                </div>
                {u.status === "generated" ? (
                  <CheckCircle2 className="h-4 w-4 text-accent" />
                ) : (
                  <Badge variant="secondary" className="rounded-full text-xs">uploaded</Badge>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
