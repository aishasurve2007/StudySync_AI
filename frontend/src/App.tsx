import { Routes, Route } from "react-router-dom";
import type { ReactNode } from "react";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { Profile } from "./pages/Profile";
import { Tasks } from "./pages/Tasks";
import { Focus } from "./pages/Focus";
import { Matching } from "./pages/Matching";
import { Rooms } from "./pages/Rooms";
import { Room } from "./pages/Room";

function Protected({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/profile" element={<Protected><Profile /></Protected>} />
      <Route path="/tasks" element={<Protected><Tasks /></Protected>} />
      <Route path="/focus" element={<Protected><Focus /></Protected>} />
      <Route path="/matches" element={<Protected><Matching /></Protected>} />
      <Route path="/rooms" element={<Protected><Rooms /></Protected>} />
      <Route path="/rooms/:id" element={<Protected><Room /></Protected>} />
    </Routes>
  );
}
