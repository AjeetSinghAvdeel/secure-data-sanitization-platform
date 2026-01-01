// src/components/ProtectedRoute.tsx
import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { auth } from "@/firebaseConfig";

interface Props {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: Props) => {
  const user = auth.currentUser;
  const sessionActive = typeof window !== "undefined" && sessionStorage.getItem("loggedIn") === "1";

  if (!user || !sessionActive) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
