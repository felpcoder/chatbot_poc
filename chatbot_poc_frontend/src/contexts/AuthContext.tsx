import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

export interface UserOut {
  id: number;
  nome: string;
  email: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserOut | null;
  login: (user: UserOut) => void; // sem token
  register: (email: string, password: string, nome?: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserOut | null>(null); 
  const [isAuthenticated, setIsAuthenticated] = useState(false);

useEffect(() => {
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    fetch("https://backendapi.devpersonalprojects.com/me", {
      credentials: "include",
    })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error("Sessão inválida");
      })
      .then(user => {
        setUser(user);
        setIsAuthenticated(true);
      })
      .catch(() => {
        localStorage.removeItem("user");
        setUser(null);
        setIsAuthenticated(false);
      });
  }
}, []);
  
const login = useCallback((userData: UserOut) => {
  setUser(userData);
  setIsAuthenticated(true);
  localStorage.setItem("user", JSON.stringify(userData));
}, []);

const register = useCallback(async (email: string, password: string, nome?: string) => {
  const response = await fetch("https://backendapi.devpersonalprojects.com/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, nome }),
    credentials: "include",
  });
  
  const data = await response.json();
  if (response.ok) {
    return true;
  } else {
    throw data;
  }
}, []);

const logout = useCallback(() => {
  setUser(null);
  setIsAuthenticated(false);
  localStorage.removeItem("user");
  
  // Opcional: avisar o backend para invalidar o cookie
  fetch("https://backendapi.devpersonalprojects.com/logout", {
    method: "POST",
    credentials: "include",
  });
}, []);

return (
  <AuthContext.Provider value={{ 
    isAuthenticated, 
    user, 
    login, 
    register, 
    logout 
  }}>
    {children}
  </AuthContext.Provider>
)};