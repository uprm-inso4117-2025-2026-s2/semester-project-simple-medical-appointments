import { useContext } from "react";
import { AuthContext } from "./AuthContext";

export function useAuth(){
    const context = useContext(AuthContext)
    if (!context) throw new Error("useAuth need to be used inside <AuthProvider>HERE</AuthProvider> component");
    return context
}
