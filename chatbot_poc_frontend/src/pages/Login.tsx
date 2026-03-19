import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";
import { Bot, Mail, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface UserOut {
  id: number;
  nome: string;
  email: string;
}

const API_URL = "https://backendapi.devpersonalprojects.com";

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nome, setNome] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (action: "login" | "register") => {
    setError("");

    if (!email || !password || (action === "register" && !nome)) {
      setError("Preencha todos os campos.");
      return;
    }

    setIsLoading(true);

    try {
      const endpoint = action === "login" ? "login" : "register";

      const body =
        action === "login"
          ? { email, password }
          : { email, password, nome };

        const response = await fetch(`${API_URL}/${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          credentials: "include", 
        });

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          const messages = data.detail.map((item: any) => item.msg).join("\n");
          setError(messages);
        } else {
          setError(data.detail || "Erro ao autenticar ou registrar.");
        }
      } else {

        login(data.user as UserOut);

        navigate("/chatbot");
      }

    } catch (err) {
      console.error("Erro de conexão:", err);
      setError("Erro de conexão com o servidor.");
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary mb-4">
            <Bot className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            Entrar na plataforma
          </h1>
          <p className="text-muted-foreground mt-2">
            Acesse o assistente inteligente da sua empresa
          </p>
        </div>

        <Card className="shadow-xl border-0 bg-card">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-display text-foreground">
              Autenticação
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10"
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit("login")}
                />
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-2">
              <Button
                variant="gold"
                size="lg"
                className="w-full text-base"
                onClick={() => handleSubmit("login")}
                disabled={isLoading}
              >
                {isLoading ? "Entrando..." : "Entrar"}
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="w-full text-base"
                onClick={() => handleSubmit("register")}
                disabled={isLoading}
              >
                Criar conta
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default Login;