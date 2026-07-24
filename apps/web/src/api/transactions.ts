import { useMutation, useQueryClient } from "@tanstack/react-query";

import { accountsQueryKey } from "@/api/accounts";
import { api } from "@/lib/api";

interface CsvUploadResult {
  imported: number;
}

export function useUploadTransactionsCsv() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ accountId, file }: { accountId: number; file: File }) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.postForm<CsvUploadResult>(
        `/v1/accounts/${accountId}/transactions/upload-csv`,
        formData,
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: accountsQueryKey });
    },
  });
}
