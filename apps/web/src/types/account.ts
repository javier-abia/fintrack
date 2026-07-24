export type AccountKind =
  | "checking"
  | "savings"
  | "credit_card"
  | "crypto"
  | "cash"
  | "investment";

export interface Account {
  id: number;
  name: string;
  kind: AccountKind;
  institution: string;
  currency: string;
  external_ref: string | null;
  is_active: boolean;
  created_at: string;
  balance: string;
}

export interface AccountCreate {
  name: string;
  kind: AccountKind;
  institution: string;
  currency: string;
  external_ref?: string | null;
}
