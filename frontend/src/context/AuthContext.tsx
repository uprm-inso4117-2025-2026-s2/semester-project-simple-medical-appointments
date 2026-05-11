import { createContext, useEffect, useState, ReactNode } from "react";
import { supabase } from "../lib/supabaseClient";
import { User } from "@supabase/supabase-js";
import { getSession, onAuthStateChange } from "../services/authService";

type AuthContextType = {
    user: User | null;
    role: string | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextType | undefined>(
    undefined,
);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const init = async () => {
            const sessionData = await getSession();
            setUser(sessionData?.user ?? null);
            setRole(sessionData?.role ?? null);
            setLoading(false);
        };
        init();

        const { data: listener } = onAuthStateChange((session: { user: any; role: any; }) => {
            setUser(session?.user ?? null);
            setRole(session?.role ?? null);
        });
        return () => listener.subscription.unsubscribe();
    }, []);

    const login = async (email: string, password: string) => {
        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        if (error) throw error;
    };

    const signup = async (email: string, password: string) => {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
    };

    const logout = async () => {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
    };

    return (
        <AuthContext.Provider value={{ user, role, loading, login, signup, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
