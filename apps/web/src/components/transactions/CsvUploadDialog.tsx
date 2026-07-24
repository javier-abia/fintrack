import { useState } from "react";

import { useUploadTransactionsCsv } from "@/api/transactions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";

export function CsvUploadDialog({ accountId }: { accountId: number }) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const upload = useUploadTransactionsCsv();

  function handleOpenChange(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen) {
      setFile(null);
      upload.reset();
    }
  }

  function handleSubmit() {
    if (!file) return;
    upload.mutate({ accountId, file });
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Upload CSV
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import transactions</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <Input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {upload.isSuccess && (
            <p className="text-sm text-muted-foreground">
              Imported {upload.data.imported} transactions.
            </p>
          )}
          {upload.isError && (
            <p className="text-sm text-destructive">
              {upload.error instanceof ApiError
                ? upload.error.message
                : "Upload failed."}
            </p>
          )}
        </div>
        <DialogFooter>
          <Button onClick={handleSubmit} disabled={!file || upload.isPending}>
            {upload.isPending ? "Uploading…" : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
