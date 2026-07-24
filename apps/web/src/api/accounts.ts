import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Account, AccountCreate } from "@/types/account";

export const accountsQueryKey = ["accounts"] as const;

export function useAccounts() {
  return useQuery({
    queryKey: accountsQueryKey,
    queryFn: () => api.get<Account[]>("/v1/accounts/"),
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AccountCreate) =>
      api.post<Account>("/v1/accounts/", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: accountsQueryKey });
    },
  });
}
