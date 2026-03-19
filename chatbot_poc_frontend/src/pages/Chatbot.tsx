import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const Chatbot = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated) navigate("/login");
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (user && messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: `Bem-vindo, ${user.nome}! Estou aqui para apoiar a squad com questões técnicas sobre modelagem de crédito, regulação bancária e arquitetura de dados para risco. Como posso ajudar hoje?`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [user, messages.length]);

  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isTyping]);

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input; 
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch('https://backendapi.devpersonalprojects.com/request_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json',
        },
        credentials: "include", 
        body: JSON.stringify({
          message: currentInput,
          conversation_id: 1
        })
      });
      if (!response.ok) throw new Error("Falha na comunicação com o servidor");

      const data = await response.json();

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.resposta_assistente, 
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Erro no fetch:", error);
      setMessages((prev) => [...prev, {
        id: "error",
        role: "assistant",
        content: "❌ **Erro ao processar requisição.** Verifique se o backend Docker está rodando ou se o token expirou.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <div className="border-b bg-card px-6 py-3">
        <h1 className="text-xl font-display font-bold text-foreground">Risco de Crédito AI Assistant</h1>
      </div>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="max-w-3xl mx-auto space-y-4 pb-4">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-card border text-card-foreground rounded-bl-md shadow-sm"
                  }`}
                >
                  <div className={`prose prose-sm dark:prose-invert max-w-none 
                    ${msg.role === "user" ? "prose-invert" : ""} 
                    prose-headings:font-bold prose-headings:mb-2 prose-headings:mt-4
                    prose-p:mb-2 prose-ul:list-disc prose-ul:ml-4`}>
                    
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4 text-accent-foreground" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isTyping && (
             <div className="flex gap-3 justify-start">
               <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0 mt-1 animate-pulse">
                 <Bot className="w-4 h-4 text-primary-foreground" />
               </div>
               <div className="bg-card border rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                 <div className="flex gap-1">
                   <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                   <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                   <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                 </div>
               </div>
             </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t bg-card p-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <Input
            placeholder="Faça sua pergunta..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            className="flex-1 h-12 rounded-xl"
            disabled={isTyping}
          />
          <Button
            variant="default"
            size="icon"
            className="h-12 w-12 rounded-xl"
            onClick={sendMessage}
            disabled={!input.trim() || isTyping}
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;