import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AccountsPage } from "@/pages/AccountsPage";
import { LoginPage } from "@/pages/LoginPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<AccountsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
